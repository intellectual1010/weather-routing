
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.conf import settings

from .checkpoint_service import haversine_meters
from .weather_service import (
    fetch_location_forecast,
    select_forecast,
    weather_grid_location,
)

logger = logging.getLogger(__name__)


def distance_km(a, b):
    return haversine_meters(
        [a[1], a[0]],
        [b[1], b[0]],
    ) / 1000.0


def select_weather_locations(checkpoints, max_locations=35):
    """
    Select geographically distributed weather-grid locations.

    Preserves all original checkpoints; only forecast
    retrieval locations are reduced.
    """

    if not checkpoints:
        return []

    if max_locations < 1:
        raise ValueError("max_locations must be positive")

    unique = {}

    for checkpoint in checkpoints:
        cell = weather_grid_location(
            checkpoint["latitude"],
            checkpoint["longitude"],
        )
        unique[cell] = cell

    locations = sorted(unique.values())

    if len(locations) <= max_locations:
        return locations

    # Choose a stable starting location.
    selected = [locations[0]]
    remaining = locations[1:]

    # Choose the point farthest from the selected set.
    min_distances = {
        location: distance_km(location, selected[0])
        for location in remaining
    }

    while remaining and len(selected) < max_locations:
        next_location = max(
            remaining,
            key=lambda location: min_distances[location],
        )

        selected.append(next_location)
        remaining.remove(next_location)
        min_distances.pop(next_location)

        for location in remaining:
            distance = distance_km(
                location, next_location
            )

            min_distances[location] = min(
                min_distances[location],
                distance,
            )

    return selected


def fetch_sampled_weather(
    checkpoints,
    max_locations=None,
):
    """
    Fetch a bounded set of forecasts concurrently.

    Map each original checkpoint to the nearest forecast
    sample while preserving its own ETA.
    """

    if not checkpoints:
        return []

    started = time.perf_counter()

    if max_locations is None:
        max_locations = getattr(
            settings, "WEATHER_MAX_LOCATIONS", 35
        )

    locations = select_weather_locations(
        checkpoints,
        max_locations=max_locations,
    )

    forecasts = {}

    max_workers = min(
        len(locations),
        getattr(settings, "WEATHER_MAX_WORKERS", 6),
    )

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:
        futures = {
            executor.submit(
                fetch_location_forecast,
                lat,
                lon,
            ): (lat, lon)
            for lat, lon in locations
        }

        for future in as_completed(futures):
            location = futures[future]
            forecasts[location] = future.result()

    max_distance_km = getattr(
        settings, "WEATHER_MAX_SAMPLE_DISTANCE_KM", 90.0
    )

    results = []
    unknown_distance_count = 0
    maximum_distance = 0.0

    for checkpoint in checkpoints:
        position = (
            checkpoint["latitude"],
            checkpoint["longitude"],
        )

        nearest = min(
            locations,
            key=lambda location: distance_km(
                position, location
            ),
        )

        nearest_distance = distance_km(
            position, nearest
        )

        maximum_distance = max(
            maximum_distance, nearest_distance
        )

        # Avoid assigning forecasts from excessively
        # distant points as though they were local.
        if nearest_distance > max_distance_km:
            results.append(None)
            unknown_distance_count += 1
            continue

        weather = select_forecast(
            forecasts[nearest],
            checkpoint["eta"],
        )

        results.append(weather)

    logger.info(
        "WEATHER SAMPLING: %d checkpoints -> %d locations; "
        "max distance %.1f km; "
        "%d distance-unavailable checkpoints; %.2fs",
        len(checkpoints),
        len(locations),
        maximum_distance,
        unknown_distance_count,
        time.perf_counter() - started,
    )

    return results
