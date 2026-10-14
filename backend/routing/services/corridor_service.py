
from bisect import bisect_left
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta, timezone

from .checkpoint_service import haversine_meters
from .risk_service import calculate_risk
from .weather_service import (
    WeatherServiceError,
    fetch_location_forecast,
    select_forecast,
)

MAX_SAMPLES = 35
MAX_WORKERS = 3
FORECAST_HOURS = 49


class CorridorForecastError(Exception):
    pass


def sample_corridor(
    coordinates,
    max_samples=MAX_SAMPLES,
):
    """
    Sample geographic points evenly along a route.

    Coordinates are GeoJSON [longitude, latitude].
    """

    if len(coordinates) < 2:
        raise CorridorForecastError(
            "Invalid route geometry."
        )

    if max_samples < 2:
        raise CorridorForecastError(
            "At least two corridor samples are required."
        )

    cumulative = [0.0]

    for a, b in zip(
        coordinates,
        coordinates[1:],
    ):
        cumulative.append(
            cumulative[-1] + haversine_meters(a, b)
        )

    total = cumulative[-1]

    if total <= 0:
        raise CorridorForecastError(
            "Zero-length route."
        )

    points = []

    for index in range(max_samples):
        target = (
            total * index / (max_samples - 1)
        )

        end = min(
            max(
                bisect_left(cumulative, target),
                1,
            ),
            len(coordinates) - 1,
        )

        before = cumulative[end - 1]
        segment_length = cumulative[end] - before

        fraction = (
            (target - before) / segment_length
            if segment_length > 0
            else 0.0
        )

        fraction = max(
            0.0,
            min(1.0, fraction),
        )

        start_coordinate = coordinates[end - 1]
        end_coordinate = coordinates[end]

        longitude = (
            start_coordinate[0]
            + (
                end_coordinate[0]
                - start_coordinate[0]
            ) * fraction
        )

        latitude = (
            start_coordinate[1]
            + (
                end_coordinate[1]
                - start_coordinate[1]
            ) * fraction
        )

        points.append({
            "index": index,
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "progress_percent": round(
                100 * index / (max_samples - 1),
                2,
            ),
        })

    return points


def _process_corridor_point(
    point,
    reference_time,
    load_weight,
):
    """
    Generate 49 hourly weather-risk snapshots
    for one geographic corridor point.
    """

    forecast_data = fetch_location_forecast(
        point["latitude"],
        point["longitude"],
    )

    hours = []

    for offset in range(FORECAST_HOURS):
        target = (
            reference_time
            + timedelta(hours=offset)
        )

        weather = select_forecast(
            forecast_data,
            target,
        )

        if weather is None:
            risk = calculate_risk(
                None,
                None,
                None,
                load_weight,
            )
        else:
            risk = calculate_risk(
                wind_mph=weather["wind_mph"],
                rain_in_hr=weather["rain_in_hr"],
                snow_in_hr=weather["snow_in_hr"],
                load_weight=load_weight,
            )

        hours.append({
            "offset": offset,
            "time": target.isoformat(),
            "weather": weather,
            "risk": risk,
        })

    return {
        **point,
        "hours": hours,
    }


def get_corridor_forecast(
    coordinates,
    reference_time,
    load_weight,
):
    """
    Return 35 corridor points with 49 hourly forecasts.

    The React response schema is unchanged.
    """

    if reference_time.tzinfo is None:
        raise CorridorForecastError(
            "Reference time must include a timezone."
        )

    reference_time = reference_time.astimezone(
        timezone.utc
    )

    points = sample_corridor(coordinates)

    results = [None] * len(points)

    try:
        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:
            future_map = {
                executor.submit(
                    _process_corridor_point,
                    point,
                    reference_time,
                    load_weight,
                ): index
                for index, point in enumerate(points)
            }

            for future in as_completed(future_map):
                index = future_map[future]
                results[index] = future.result()

    except WeatherServiceError as exc:
        raise CorridorForecastError(
            "Unable to retrieve corridor weather forecasts."
        ) from exc

    return {
        "reference_time": reference_time.isoformat(),
        "hour_count": FORECAST_HOURS,
        "sample_count": len(results),
        "points": results,
    }
