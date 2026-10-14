
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import math
import requests
import hashlib
import json
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

BATCH_SIZE = 5
MAX_WORKERS = 2
CM_TO_INCH = 1 / 2.54


class WeatherServiceError(Exception):
    pass


def parse_utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    if value.tzinfo is None:
        raise WeatherServiceError(
            "Checkpoint ETA must include a timezone."
        )

    return value.astimezone(timezone.utc)


def _fetch_weather_batch_uncached(points):
    """
    Fetch hourly forecasts for multiple locations.
    Each point must include latitude, longitude and eta.
    """

    if not points:
        return []

    dates = [parse_utc(p["eta"]) for p in points]

    now = datetime.now(timezone.utc)
    if min(dates) < now:
        raise WeatherServiceError(
            "Checkpoint arrival is in the past."
        )

    # The standard forecast API supports up to 16 days.
    if max(dates).timestamp() > now.timestamp() + 15 * 86400:
        raise WeatherServiceError(
            "Checkpoint ETA is beyond the supported "
            "forecast planning window."
        )

    params = {
        "latitude": ",".join(
            str(p["latitude"]) for p in points
        ),
        "longitude": ",".join(
            str(p["longitude"]) for p in points
        ),
        "hourly": "wind_speed_10m,rain,snowfall",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "GMT",
        "start_date": min(dates).date().isoformat(),
        "end_date": max(dates).date().isoformat(),
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=40,
        )

        if not response.ok:
            logger.error(
                "Open-Meteo HTTP %s: %s",
                response.status_code,
                response.text[:1000],
            )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise WeatherServiceError(
            "Open-Meteo forecast request failed."
        ) from exc

    if isinstance(payload, dict):
        payload = [payload]

    if len(payload) != len(points):
        raise WeatherServiceError(
            "Unexpected number of weather responses."
        )

    return [
        select_forecast(data, point["eta"])
        for data, point in zip(payload, points)
    ]

def fetch_weather_batch(points):
    """
    Cache the forecast response for identical checkpoint
    coordinates and ETA values for 15 minutes.
    """

    if not points:
        return []

    cache_input = [
        {
            "lat": round(float(p["latitude"]), 3),
            "lon": round(float(p["longitude"]), 3),
            "eta_hour": parse_utc(p["eta"]).replace(
                minute=0,
                second=0,
                microsecond=0,
            ).isoformat(),
        }
        for p in points
    ]

    raw_key = json.dumps(
        cache_input,
        sort_keys=True,
        separators=(",", ":"),
    )

    digest = hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()

    cache_key = f"weather:batch:v1:{digest}"

    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    result = _fetch_weather_batch_uncached(points)

    cache.set(cache_key, result, timeout=900)

    return result

def select_forecast(data, eta):
    """
    Select the nearest hourly forecast to checkpoint ETA.

    Hourly precipitation values represent an hour,
    so this is an approximation of conditions at arrival.
    """

    target = parse_utc(eta)
    hourly = data.get("hourly") or {}

    times = hourly.get("time") or []
    if not times:
        return None

    parsed_times = [
        datetime.fromisoformat(t).replace(
            tzinfo=timezone.utc
        )
        for t in times
    ]

    index = min(
        range(len(parsed_times)),
        key=lambda i: abs(
            (parsed_times[i] - target).total_seconds()
        ),
    )

    if abs(
        (parsed_times[index] - target).total_seconds()
    ) > 3600:
        return None

    def number(field):
        values = hourly.get(field) or []
        if index >= len(values):
            return None

        value = values[index]

        if value is None:
            return None

        value = float(value)
        return value if math.isfinite(value) else None

    wind = number("wind_speed_10m")
    rain = number("rain")
    snow_cm = number("snowfall")

    if None in (wind, rain, snow_cm):
        return None

    if min(wind, rain, snow_cm) < 0:
        return None

    return {
        "wind_mph": wind,
        "rain_in_hr": rain,
        "snow_in_hr": snow_cm * CM_TO_INCH,
        "forecast_time": parsed_times[index].isoformat(),
        "source": "open-meteo",
    }


def fetch_checkpoint_weather(checkpoints):
    """
    Fetch forecasts in batches, preserving checkpoint order.
    """

    if not checkpoints:
        return []

    batches = [
        checkpoints[i:i + BATCH_SIZE]
        for i in range(0, len(checkpoints), BATCH_SIZE)
    ]

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:
        results = list(
            executor.map(fetch_weather_batch, batches)
        )

    return [
        weather
        for batch in results
        for weather in batch
    ]
