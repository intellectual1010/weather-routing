
import math
from datetime import timedelta

METERS_PER_MILE = 1609.344
EARTH_RADIUS_METERS = 6371008.8


def haversine_meters(a, b):
    """Geographic distance between [lon, lat] coordinates."""

    lon1, lat1 = map(math.radians, a[:2])
    lon2, lat2 = map(math.radians, b[:2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * EARTH_RADIUS_METERS * math.asin(
        min(1.0, math.sqrt(h))
    )


def interpolate_coordinate(a, b, ratio):
    """Interpolate a point along a short geometry segment."""

    return [
        a[0] + (b[0] - a[0]) * ratio,
        a[1] + (b[1] - a[1]) * ratio,
    ]


def generate_checkpoints(
    route: dict,
    departure_time,
    interval_miles: int = 25,
) -> list:
    """
    Sample points along the returned road geometry.

    Uses provider distance to determine mile markers.
    ETAs assume travel time scales with distance; future
    versions can use segment-level traffic timing.
    """

    if interval_miles not in (10, 25, 50):
        raise ValueError("Interval must be 10, 25, or 50 miles.")

    coordinates = route["geometry"]["coordinates"]

    if len(coordinates) < 2:
        raise ValueError("Route needs at least two coordinates.")

    total_meters = route["distance_meters"]
    duration_seconds = route["duration_seconds"]

    if total_meters <= 0 or duration_seconds < 0:
        raise ValueError("Invalid route distance or duration.")

    # Cumulative geometric distance at each vertex.
    cumulative = [0.0]

    for i in range(1, len(coordinates)):
        length = haversine_meters(
            coordinates[i - 1],
            coordinates[i],
        )
        cumulative.append(cumulative[-1] + length)

    geometry_length = cumulative[-1]

    if geometry_length <= 0:
        raise ValueError("Route has zero geometry length.")

    spacing = interval_miles * METERS_PER_MILE

    # Always include origin and destination.
    targets = [0.0]
    distance = spacing

    while distance < total_meters:
        targets.append(distance)
        distance += spacing

    targets.append(total_meters)

    checkpoints = []
    segment_index = 1

    for index, target in enumerate(targets):
        progress = target / total_meters
        geometry_target = progress * geometry_length

        while (
            segment_index < len(cumulative) - 1
            and cumulative[segment_index] < geometry_target
        ):
            segment_index += 1

        before = cumulative[segment_index - 1]
        after = cumulative[segment_index]

        ratio = (
            (geometry_target - before) / (after - before)
            if after > before
            else 0.0
        )

        point = interpolate_coordinate(
            coordinates[segment_index - 1],
            coordinates[segment_index],
            max(0.0, min(1.0, ratio)),
        )

        elapsed_seconds = duration_seconds * progress
        eta = departure_time + timedelta(
            seconds=elapsed_seconds
        )

        checkpoints.append({
            "id": f"{route['id']}_cp_{index}",
            "index": index,
            "mile_marker": round(
                target / METERS_PER_MILE, 2
            ),
            "latitude": round(point[1], 6),
            "longitude": round(point[0], 6),
            "coordinates": [
                round(point[0], 6),
                round(point[1], 6),
            ],
            "eta": eta.isoformat(),
            "elapsed_minutes": round(
                elapsed_seconds / 60, 2
            ),
            "progress_percent": round(progress * 100, 2),
        })

    # Attribute surrounding mileage to each checkpoint.
    # Interior points represent half the distance to
    # their previous and next neighbors.
    for i, checkpoint in enumerate(checkpoints):
        left = (
            0.0 if i == 0
            else (
                checkpoints[i - 1]["mile_marker"]
                + checkpoint["mile_marker"]
            ) / 2
        )

        right = (
            total_meters / METERS_PER_MILE
            if i == len(checkpoints) - 1
            else (
                checkpoint["mile_marker"]
                + checkpoints[i + 1]["mile_marker"]
            ) / 2
        )

        checkpoint["represented_miles"] = round(
            max(0.0, right - left), 3
        )

    return checkpoints
