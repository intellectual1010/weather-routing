
import requests
from django.conf import settings

METERS_TO_MILES = 0.000621371


class MapboxRoutingError(Exception):
    pass


def get_mapbox_routes(
    origin_coords: list,
    destination_coords: list,
) -> dict:
    """
    Retrieve up to 3 genuine routes from Mapbox Directions.
    Coordinates use [longitude, latitude].
    """

    token = settings.MAPBOX_ACCESS_TOKEN

    if not token:
        raise MapboxRoutingError(
            "Mapbox access token is not configured."
        )

    start = f"{origin_coords[0]},{origin_coords[1]}"
    end = f"{destination_coords[0]},{destination_coords[1]}"

    url = (
        f"{settings.MAPBOX_BASE_URL}"
        "/directions/v5/mapbox/driving/"
        f"{start};{end}"
    )

    params = {
        "access_token": token,
        "alternatives": "true",
        "geometries": "geojson",
        "overview": "full",
        "steps": "false",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()

    except (requests.RequestException, ValueError) as exc:
        raise MapboxRoutingError(
            "Mapbox routing request failed."
        ) from exc

    if data.get("code") != "Ok":
        raise MapboxRoutingError(
            "Mapbox could not calculate a route."
        )

    raw_routes = data.get("routes", [])

    if not raw_routes:
        raise MapboxRoutingError(
            "No driving routes were found."
        )

    routes = []
    seen = set()

    for route in raw_routes:
        geometry = route.get("geometry", {})
        coordinates = geometry.get("coordinates", [])

        if len(coordinates) < 2:
            continue

        signature = tuple(
            tuple(point[:2]) for point in coordinates
        )

        if signature in seen:
            continue

        seen.add(signature)

        distance = route["distance"]
        duration = route["duration"]
        index = len(routes) + 1

        routes.append({
            "id": f"route_{index}",
            "name": f"Route {index}",
            "distance_miles": round(
                distance * METERS_TO_MILES, 2
            ),
            "distance_meters": distance,
            "duration_seconds": duration,
            "duration_minutes": round(duration / 60, 2),
            "duration_hours": round(duration / 3600, 2),
            "geometry": geometry,
            "provider": "mapbox",
            "profile": "driving",
        })

        if len(routes) == 3:
            break

    if not routes:
        raise MapboxRoutingError(
            "Mapbox returned no usable route geometry."
        )

    return {
        "routes": routes,
        "route_count": len(routes),
        "has_three_routes": len(routes) == 3,
        "message": (
            None if len(routes) == 3
            else (
                f"Mapbox found {len(routes)} distinct route(s). "
                "Additional viable alternatives were not returned."
            )
        ),
    }
