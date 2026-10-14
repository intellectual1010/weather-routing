
import logging
import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class GeocodingError(Exception):
    pass


def geocode_location(location: str) -> dict:
    """Convert a location name to geographic coordinates."""

    if not settings.ORS_API_KEY:
        raise GeocodingError("ORS API key is not configured.")

    url = f"{settings.ORS_BASE_URL}/geocode/search"

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": settings.ORS_API_KEY,
                "Accept": "application/json",
            },
            params={
                "text": location,
                "size": 1,
            },
            timeout=15,
        )
        response.raise_for_status()

        features = response.json().get("features", [])

    except (requests.RequestException, ValueError) as exc:
        http_status = getattr(getattr(exc, "response", None), "status_code", None)
        logger.warning("ORS geocoding failure: status=%s error=%s", http_status, type(exc).__name__)
        raise GeocodingError(
            "Geocoding provider request failed."
        ) from exc

    if not features:
        raise GeocodingError(
            f"No location found for '{location}'."
        )

    feature = features[0]
    longitude, latitude = feature["geometry"]["coordinates"]

    return {
        "name": feature["properties"].get("label", location),
        "latitude": latitude,
        "longitude": longitude,
        "coordinates": [longitude, latitude],
    }
