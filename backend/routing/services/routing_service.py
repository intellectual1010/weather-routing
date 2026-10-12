
import requests
from django.conf import settings

METERS_TO_MILES = 0.000621371
ALTERNATIVE_ROUTE_LIMIT_METERS = 100_000


class RoutingError(Exception):
    pass


def request_directions(
    origin_coords: list,
    destination_coords: list,
    alternatives: bool = False,
) -> list:
    """Request route geometries from OpenRouteService."""

    url = (
        f"{settings.ORS_BASE_URL}"
        "/v2/directions/driving-car/geojson"
    )

    payload = {
        "coordinates": [
            origin_coords,
            destination_coords,
        ],
        "instructions": False,
    }

    if alternatives:
        payload["alternative_routes"] = {
            "target_count": 3,
            "share_factor": 0.6,
            "weight_factor": 1.8,
        }

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": settings.ORS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/geo+json",
            },
            json=payload,
            timeout=45,
        )

        if not response.ok:
            raise RoutingError(
                f"Routing provider returned HTTP "
                f"{response.status_code}: "
                f"{response.text[:300]}"
            )

        features = response.json().get("features", [])

    except (requests.RequestException, ValueError) as exc:
        raise RoutingError(
            "Routing provider request failed."
        ) from exc

    if not features:
        raise RoutingError("No driving routes were found.")

    return features


def format_route(feature: dict, index: int) -> dict:
    """Convert an ORS GeoJSON feature to our API format."""

    summary = feature["properties"]["summary"]

    distance_meters = summary["distance"]
    duration_seconds = summary["duration"]

    return {
        "id": f"route_{index}",
        "name": f"Route {index}",
        "distance_miles": round(
            distance_meters * METERS_TO_MILES, 2
        ),
        "duration_minutes": round(
            duration_seconds / 60, 2
        ),
        "duration_hours": round(
            duration_seconds / 3600, 2
        ),
        "geometry": feature["geometry"],
    }


def get_routes(
    origin_coords: list,
    destination_coords: list,
) -> dict:
    """Get all available genuine route alternatives."""

    if not settings.ORS_API_KEY:
        raise RoutingError("ORS API key is not configured.")

    # First request the normal route.
    primary = request_directions(
        origin_coords,
        destination_coords,
    )

    distance_meters = primary[0]["properties"]["summary"]["distance"]

    # ORS public alternative-route capability is distance-limited.
    if distance_meters >= ALTERNATIVE_ROUTE_LIMIT_METERS:
        features = primary
        message = (
            "OpenRouteService alternative routes are not "
            "available for this long-distance trip. "
            "A second routing provider is required "
            "to obtain three long-haul alternatives."
        )
    else:
        try:
            features = request_directions(
                origin_coords,
                destination_coords,
                alternatives=True,
            )
            message = None
        except RoutingError:
            features = primary
            message = (
                "Alternative routes could not be retrieved. "
                "Showing the available primary route."
            )

    # Remove exact geometry duplicates.
    unique_features = []
    seen = set()

    for feature in features:
        coordinates = feature["geometry"]["coordinates"]
        signature = str(coordinates)

        if signature in seen:
            continue

        seen.add(signature)
        unique_features.append(feature)

    routes = [
        format_route(feature, index)
        for index, feature in enumerate(
            unique_features[:3], start=1
        )
    ]

    if len(routes) < 3 and message is None:
        message = (
            "The routing provider returned fewer than "
            "three distinct route options."
        )

    return {
        "routes": routes,
        "route_count": len(routes),
        "has_three_routes": len(routes) == 3,
        "message": message,
    }
