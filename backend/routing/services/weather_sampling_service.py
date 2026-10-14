from math import cos, radians, sqrt

from .weather_service import (
    fetch_checkpoint_weather,
    select_forecast,
    fetch_location_forecast,
)


def geographical_distance(a, b):
    """Approximate geographic distance in kilometers."""
    lat1, lon1 = a
    lat2, lon2 = b

    lat_km = (lat2 - lat1) * 111.32
    lon_km = (lon2 - lon1) * 111.32 * cos(
        radians((lat1 + lat2) / 2)
    )

    return sqrt(lat_km ** 2 + lon_km ** 2)


def build_weather_sample_points(
    checkpoints,
    minimum_spacing_km=40,
):
    """Select forecast sample locations across all routes."""
    samples = []

    for checkpoint in checkpoints:
        location = (
            checkpoint["latitude"],
            checkpoint["longitude"],
        )

        if not samples or all(
            geographical_distance(
                location,
                (
                    sample["latitude"],
                    sample["longitude"],
                ),
            ) >= minimum_spacing_km
            for sample in samples
        ):
            samples.append(checkpoint)

    return samples


def fetch_sampled_weather(
    checkpoints,
    minimum_spacing_km=40,
):
    """Fetch sampled forecasts and map them to checkpoints."""

    if not checkpoints:
        return []

    samples = build_weather_sample_points(
        checkpoints,
        minimum_spacing_km,
    )

    forecasts = {}

    for sample in samples:
        key = (
            sample["latitude"],
            sample["longitude"],
        )

        forecasts[key] = fetch_location_forecast(
            sample["latitude"],
            sample["longitude"],
        )

    results = []

    for checkpoint in checkpoints:
        closest = min(
            samples,
            key=lambda sample: geographical_distance(
                (
                    checkpoint["latitude"],
                    checkpoint["longitude"],
                ),
                (
                    sample["latitude"],
                    sample["longitude"],
                ),
            ),
        )

        key = (
            closest["latitude"],
            closest["longitude"],
        )

        results.append(
            select_forecast(
                forecasts[key],
                checkpoint["eta"],
            )
        )

    return results