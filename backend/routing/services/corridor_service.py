
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from bisect import bisect_left

import requests

from .checkpoint_service import haversine_meters
from .risk_service import calculate_risk
from .weather_service import (
    OPEN_METEO_URL,
    select_forecast,
)

MAX_SAMPLES = 35
BATCH_SIZE = 10


class CorridorForecastError(Exception):
    pass


def sample_corridor(coordinates, max_samples=MAX_SAMPLES):
    """Sample evenly spaced points along a road LineString."""

    if len(coordinates) < 2:
        raise CorridorForecastError("Invalid route geometry.")

    cumulative = [0.0]

    for a, b in zip(coordinates, coordinates[1:]):
        cumulative.append(
            cumulative[-1] + haversine_meters(a, b)
        )

    total = cumulative[-1]

    if total <= 0:
        raise CorridorForecastError("Zero-length route.")

    points = []

    for index in range(max_samples):
        target = total * index / (max_samples - 1)
        end = min(
            max(bisect_left(cumulative, target), 1),
            len(coordinates) - 1,
        )

        start_distance = cumulative[end - 1]
        segment_length = cumulative[end] - start_distance

        fraction = (
            (target - start_distance) / segment_length
            if segment_length > 0 else 0.0
        )
        fraction = min(1.0, max(0.0, fraction))

        a, b = coordinates[end - 1], coordinates[end]

        lon = a[0] + (b[0] - a[0]) * fraction
        lat = a[1] + (b[1] - a[1]) * fraction

        points.append({
            "index": index,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "progress_percent": round(
                100 * index / (max_samples - 1), 2
            ),
        })

    return points


def _fetch_batch(points, reference_time, load_weight):
    start_date = reference_time.date().isoformat()
    end_date = (
        reference_time + timedelta(hours=49)
    ).date().isoformat()

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
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=40,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise CorridorForecastError(
            "Corridor weather service unavailable."
        ) from exc

    if isinstance(data, dict):
        data = [data]

    if len(data) != len(points):
        raise CorridorForecastError(
            "Weather response count mismatch."
        )

    result = []

    for point, forecast in zip(points, data):
        hours = []

        for offset in range(49):
            target = reference_time + timedelta(hours=offset)
            weather = select_forecast(
                forecast,
                target.isoformat(),
            )

            if weather is None:
                risk = calculate_risk(
                    None, None, None, load_weight
                )
            else:
                risk = calculate_risk(
                    weather["wind_mph"],
                    weather["rain_in_hr"],
                    weather["snow_in_hr"],
                    load_weight,
                )

            hours.append({
                "offset": offset,
                "time": target.isoformat(),
                "weather": weather,
                "risk": risk,
            })

        result.append({
            **point,
            "hours": hours,
        })

    return result


def get_corridor_forecast(
    coordinates,
    reference_time,
    load_weight,
):
    """Retrieve 49 forecast snapshots for route corridor."""

    reference_time = reference_time.astimezone(timezone.utc)

    samples = sample_corridor(coordinates)

    batches = [
        samples[i:i + BATCH_SIZE]
        for i in range(0, len(samples), BATCH_SIZE)
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(
            lambda batch: _fetch_batch(
                batch, reference_time, load_weight
            ),
            batches,
        ))

    return {
        "reference_time": reference_time.isoformat(),
        "hour_count": 49,
        "sample_count": len(samples),
        "points": [
            point
            for batch in results
            for point in batch
        ],
    }
