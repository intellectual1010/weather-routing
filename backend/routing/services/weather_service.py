
import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests
from django.conf import settings
from django.core.cache import cache
from math import floor
import os

logger = logging.getLogger(__name__)

WEATHERAPI_URL = (
    f"{settings.WEATHERAPI_BASE_URL.rstrip('/')}/forecast.json"
)

WEATHER_GRID_DEGREES = float(
    os.getenv("WEATHER_GRID_DEGREES", "0.35")
)

WEATHER_MAX_WORKERS = int(
    os.getenv("WEATHER_MAX_WORKERS", "6")
)

WEATHER_CACHE_SECONDS = int(
    os.getenv("WEATHER_CACHE_SECONDS", "1800")
)

MAX_WORKERS = getattr(settings, "WEATHER_MAX_WORKERS", 6)
CACHE_SECONDS = getattr(settings, "WEATHER_CACHE_SECONDS", 1800)
MAX_FORECAST_DAYS = 3


class WeatherServiceError(Exception):
    pass


class WeatherQuotaExceeded(WeatherServiceError):
    pass


def parse_utc(value):
    """Convert an aware datetime or ISO string to UTC."""

    if isinstance(value, str):
        value = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    if value.tzinfo is None:
        raise WeatherServiceError(
            "Forecast timestamps must include a timezone."
        )

    return value.astimezone(timezone.utc)


def _valid_number(value):
    if value is None or isinstance(value, bool):
        return None

    try:
        number = float(value)
    except (ValueError, TypeError):
        return None

    if not math.isfinite(number) or number < 0:
        return None

    return number

def weather_grid_location(latitude, longitude):
    """
    Return the center of a geographic forecast cell.

    Every coordinate in the same cell uses the same
    forecast location, allowing safe cache-key reuse.
    """

    grid = getattr(settings, "WEATHER_GRID_DEGREES", 0.35)

    if not 0 < grid <= 1:
        raise WeatherServiceError(
            "WEATHER_GRID_DEGREES must be between 0 and 1."
        )

    latitude = float(latitude)
    longitude = float(longitude)

    cell_lat = (
        floor(latitude / grid) + 0.5
    ) * grid

    cell_lon = (
        floor(longitude / grid) + 0.5
    ) * grid

    return (
        round(max(-90, min(90, cell_lat)), 6),
        round(max(-180, min(180, cell_lon)), 6),
    )


def _cache_key(latitude, longitude):
    lat, lon = weather_grid_location(
        latitude, longitude
    )

    return f"weatherapi:forecast:v2:{lat:.6f}:{lon:.6f}"


def fetch_location_forecast(latitude, longitude):
    """
    Fetch a 3-day hourly forecast for one location.

    WeatherAPI's free forecast endpoint uses one
    geographic location per request.
    """

    if not settings.WEATHERAPI_KEY:
        raise WeatherServiceError(
            "WEATHERAPI_KEY is not configured."
        )

    key = _cache_key(latitude, longitude)

    cached = cache.get(key)
    if cached is not None:
        return cached

    grid_lat, grid_lon = weather_grid_location(
        latitude, longitude
    )

    params = {
        "key": settings.WEATHERAPI_KEY,
        "q": f"{grid_lat},{grid_lon}",
        "days": MAX_FORECAST_DAYS,
        "aqi": "no",
        "alerts": "no",
    }

    try:
        response = requests.get(
            WEATHERAPI_URL,
            params=params,
            timeout=20,
        )

        if response.status_code == 429:
            raise WeatherQuotaExceeded(
                "WeatherAPI request limit exceeded."
            )

        if not response.ok:
            logger.error(
                "WeatherAPI request failed: HTTP %s, body=%s",
                response.status_code,
                response.text[:300],
            )

            raise WeatherServiceError(
                "Weather provider temporarily unavailable."
            )

        data = response.json()

    except requests.RequestException as exc:
        raise WeatherServiceError(
            "Weather provider network request failed."
        ) from exc

    except ValueError as exc:
        raise WeatherServiceError(
            "Weather provider returned invalid JSON."
        ) from exc

    if not data.get("forecast", {}).get("forecastday"):
        raise WeatherServiceError(
            "Weather provider returned no forecast."
        )

    cache.set(key, data, timeout=settings.WEATHER_CACHE_SECONDS,)

    return data


def select_forecast(data, eta):
    """
    Select the nearest available forecast hour using
    WeatherAPI time_epoch (UTC Unix timestamps).

    Returns None when forecast coverage is missing.
    """

    target = parse_utc(eta)
    target_timestamp = target.timestamp()

    hours = []

    for forecast_day in data.get(
        "forecast", {}
    ).get("forecastday", []):
        hours.extend(forecast_day.get("hour", []))

    if not hours:
        return None

    valid_hours = [
        hour for hour in hours
        if hour.get("time_epoch") is not None
    ]

    if not valid_hours:
        return None

    hour = min(
        valid_hours,
        key=lambda item: abs(
            float(item["time_epoch"]) - target_timestamp
        ),
    )

    forecast_timestamp = float(hour["time_epoch"])

    # Do not silently use distant forecasts.
    if abs(forecast_timestamp - target_timestamp) > 1800:
        return None

    wind = _valid_number(hour.get("wind_mph"))
    precipitation = _valid_number(hour.get("precip_in"))
    snow_cm = _valid_number(hour.get("snow_cm"))

    if any(
        value is None
        for value in (wind, precipitation, snow_cm)
    ):
        return None

    return {
        "wind_mph": wind,
        # WeatherAPI precipitation includes liquid
        # equivalent precipitation, potentially snow.
        # Used as a conservative precipitation proxy.
        "rain_in_hr": precipitation,
        "snow_in_hr": snow_cm / 2.54,
        "forecast_time": datetime.fromtimestamp(
            forecast_timestamp,
            tz=timezone.utc,
        ).isoformat(),
        "source": "weatherapi",
    }


def _fetch_one_checkpoint(checkpoint):
    data = fetch_location_forecast(
        checkpoint["latitude"],
        checkpoint["longitude"],
    )

    return select_forecast(
        data,
        checkpoint["eta"],
    )


def fetch_weather_batch(points):
    """Fetch weather for a batch, preserving order."""

    if not points:
        return []

    results = [None] * len(points)

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:
        future_map = {
            executor.submit(
                _fetch_one_checkpoint, point
            ): index
            for index, point in enumerate(points)
        }

        for future in as_completed(future_map):
            index = future_map[future]
            results[index] = future.result()

    return results


def fetch_checkpoint_weather(checkpoints):
    """
    Return weather results in original checkpoint order.

    Missing forecast hours are returned as None,
    allowing the risk engine to mark them 'unknown'.
    """

    if not checkpoints:
        return []

    # Deduplicate locations within one request.
    unique_locations = {}

    for checkpoint in checkpoints:
        key = _cache_key(
            checkpoint["latitude"],
            checkpoint["longitude"],
        )

        if key not in unique_locations:
            unique_locations[key] = checkpoint

    locations = list(unique_locations.items())
    forecasts = {}

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:
        future_map = {
            executor.submit(
                fetch_location_forecast,
                point["latitude"],
                point["longitude"],
            ): key
            for key, point in locations
        }

        for future in as_completed(future_map):
            key = future_map[future]
            forecasts[key] = future.result()

    results = []

    for checkpoint in checkpoints:
        key = _cache_key(
            checkpoint["latitude"],
            checkpoint["longitude"],
        )

        results.append(
            select_forecast(
                forecasts[key],
                checkpoint["eta"],
            )
        )

    return results
