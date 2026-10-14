
import logging
import math

import requests
from django.conf import settings

from .checkpoint_service import haversine_meters
from .geocoding_service import (
    GeocodingError,
    geocode_location,
)

logger = logging.getLogger(__name__)

METERS_TO_MILES = 0.000621371

MAX_ROUTES = 3
MAX_WAYPOINT_ATTEMPTS = 4
MAX_DETOUR_FACTOR = 1.45

# A candidate must diverge from existing routes over
# a meaningful portion of its sampled geometry.
MIN_DIVERGENCE_METERS = 12000
MIN_DIVERGENCE_FRACTION = 0.18


class MapboxRoutingError(Exception):
    pass


# Candidate corridor cities for demo and assessment
# scenarios. Reverse-direction requests are supported.
CORRIDOR_WAYPOINTS = {
    frozenset(("seattle", "phoenix")): [
        "Sacramento, California",
        "Reno, Nevada",
        "Las Vegas, Nevada",
    ],
    frozenset(("los angeles", "denver")): [
        "Albuquerque, New Mexico",
        "Flagstaff, Arizona",
        "Salt Lake City, Utah",
    ],
    frozenset(("chicago", "atlanta")): [
        "Louisville, Kentucky",
        "Indianapolis, Indiana",
        "Birmingham, Alabama",
    ],
    frozenset(("seattle", "denver")): [
        "Boise, Idaho",
        "Salt Lake City, Utah",
        "Spokane, Washington",
        "Billings, Montana",
    ],
}


def city_key(name):
    """Extract a city name from typical input text."""
    return name.split(",")[0].strip().lower()


def get_candidate_waypoints(origin_name, destination_name):
    key = frozenset((
        city_key(origin_name),
        city_key(destination_name),
    ))
    return CORRIDOR_WAYPOINTS.get(key, [])


def request_mapbox_directions(
    coordinates,
    alternatives=False,
):
    """
    Request genuine road directions through 2 or more
    [longitude, latitude] coordinates.
    """

    token = settings.MAPBOX_ACCESS_TOKEN

    if not token:
        raise MapboxRoutingError(
            "Mapbox access token is not configured."
        )

    if not 2 <= len(coordinates) <= 25:
        raise MapboxRoutingError(
            "Mapbox requires 2 to 25 coordinates."
        )

    coordinate_string = ";".join(
        f"{float(lon)},{float(lat)}"
        for lon, lat in coordinates
    )

    url = (
        f"{settings.MAPBOX_BASE_URL.rstrip('/')}"
        "/directions/v5/mapbox/driving/"
        f"{coordinate_string}"
    )

    params = {
        "access_token": token,
        "alternatives": (
            "true" if alternatives else "false"
        ),
        "geometries": "geojson",
        "overview": "full",
        "steps": "false",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=40,
        )
        response.raise_for_status()
        payload = response.json()

    except (requests.RequestException, ValueError) as exc:
        logger.warning(
            "Mapbox directions request failed: %s",
            type(exc).__name__,
        )
        raise MapboxRoutingError(
            "Mapbox routing request failed."
        ) from exc

    if payload.get("code") != "Ok":
        raise MapboxRoutingError(
            "Mapbox could not calculate this route."
        )

    routes = payload.get("routes", [])

    if not routes:
        raise MapboxRoutingError(
            "No driving routes were returned."
        )

    return routes


def sample_coordinates(coordinates, count=120):
    """Return an evenly indexed subset for comparison."""

    if len(coordinates) <= count:
        return coordinates

    return [
        coordinates[
            round(
                i * (len(coordinates) - 1)
                / (count - 1)
            )
        ]
        for i in range(count)
    ]


def divergence_fraction(candidate, existing):
    """
    Approximate how much of a candidate's road geometry
    is at least 12 km from an existing route.

    This is a geographic distinctness heuristic.
    It is not a precise network-overlap calculation.
    """

    candidate_points = sample_coordinates(
        candidate["geometry"]["coordinates"],
        count=100,
    )

    existing_points = sample_coordinates(
        existing["geometry"]["coordinates"],
        count=200,
    )

    divergent_count = 0

    for point in candidate_points:
        minimum = min(
            haversine_meters(point, other)
            for other in existing_points
        )

        if minimum >= MIN_DIVERGENCE_METERS:
            divergent_count += 1

    return divergent_count / len(candidate_points)


def is_distinct_route(candidate, existing_routes):
    """
    Reject routes that closely duplicate any
    existing option.
    """

    candidate_geometry = candidate["geometry"]

    if candidate_geometry.get("type") != "LineString":
        return False

    if len(candidate_geometry.get("coordinates", [])) < 2:
        return False

    for existing in existing_routes:
        fraction = divergence_fraction(
            candidate, existing
        )

        if fraction < MIN_DIVERGENCE_FRACTION:
            return False

    return True


def format_route(raw, index, via_city=None):
    distance = float(raw["distance"])
    duration = float(raw["duration"])

    result = {
        "id": f"route_{index}",
        "name": f"Route {index}",
        "distance_miles": round(
            distance * METERS_TO_MILES, 2
        ),
        "distance_meters": distance,
        "duration_seconds": duration,
        "duration_minutes": round(duration / 60, 2),
        "duration_hours": round(duration / 3600, 2),
        "geometry": raw["geometry"],
        "provider": "mapbox",
        "profile": "driving",
    }

    # Additional metadata won't break the frontend.
    if via_city:
        result["via_city"] = via_city

    return result


def get_mapbox_routes(
    origin_coords,
    destination_coords,
    origin_name=None,
    destination_name=None,
):
    """
    Return up to three geographically distinct road routes.

    1. Get normal Mapbox alternatives.
    2. Request additional routes through curated cities.
    3. Reject major detours and near-duplicates.
    """

    primary_results = request_mapbox_directions(
        [origin_coords, destination_coords],
        alternatives=True,
    )

    # Always retain Mapbox's first primary route.
    routes = [
        format_route(primary_results[0], 1)
    ]

    primary_distance = routes[0]["distance_meters"]

    # Add distinct provider alternatives.
    for raw in primary_results[1:]:
        candidate = format_route(
            raw, len(routes) + 1
        )

        if (
            candidate["distance_meters"]
            <= primary_distance * MAX_DETOUR_FACTOR
            and is_distinct_route(candidate, routes)
        ):
            routes.append(candidate)

        if len(routes) >= MAX_ROUTES:
            break

    # Supplement with alternative corridor requests.
    if (
        len(routes) < MAX_ROUTES
        and origin_name
        and destination_name
    ):
        waypoint_names = get_candidate_waypoints(
            origin_name,
            destination_name,
        )

        for via_city in waypoint_names[
            :MAX_WAYPOINT_ATTEMPTS
        ]:
            if len(routes) >= MAX_ROUTES:
                break

            try:
                waypoint = geocode_location(via_city)

                waypoint_coords = waypoint["coordinates"]

                waypoint_routes = request_mapbox_directions(
                    [
                        origin_coords,
                        waypoint_coords,
                        destination_coords,
                    ],
                    alternatives=False,
                )

                for raw in waypoint_routes:
                    candidate = format_route(
                        raw,
                        len(routes) + 1,
                        via_city=via_city,
                    )

                    if (
                        candidate["distance_meters"]
                        > primary_distance * MAX_DETOUR_FACTOR
                    ):
                        continue

                    if not is_distinct_route(
                        candidate, routes
                    ):
                        continue

                    routes.append(candidate)
                    break

            except (
                GeocodingError,
                MapboxRoutingError,
                KeyError,
                ValueError,
            ) as exc:
                logger.warning(
                    "Failed waypoint candidate %s: %s",
                    via_city,
                    type(exc).__name__,
                )
                continue

    # Assign stable, sequential identifiers.
    for index, route in enumerate(routes, start=1):
        route["id"] = f"route_{index}"
        route["name"] = f"Route {index}"

    count = len(routes)

    return {
        "routes": routes,
        "route_count": count,
        "has_three_routes": count == 3,
        "message": (
            None if count == 3
            else (
                f"Found {count} distinct driving route(s). "
                "Additional sufficiently different "
                "routes were not available."
            )
        ),
    }
