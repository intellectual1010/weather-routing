
import logging
import requests

from django.conf import settings

logger = logging.getLogger(__name__)

MAPBOX_GEOCODING_URL = (
    "https://api.mapbox.com/search/geocode/v6/forward"
)


class GeocodingError(Exception):
    pass


def geocode_location(query):
    token = settings.MAPBOX_ACCESS_TOKEN

    if not token:
        raise GeocodingError(
            "Mapbox access token is not configured."
        )

    try:
        response = requests.get(
            MAPBOX_GEOCODING_URL,
            params={
                "q": query,
                "access_token": token,
                "limit": 1,
                "types": "place,locality",
                "autocomplete": "false",
                "permanent": "false",
            },
            timeout=12,
        )

        response.raise_for_status()

        features = response.json().get(
            "features", []
        )

        if not features:
            raise GeocodingError(
                f"Location not found: {query}"
            )

        feature = features[0]

        coordinates = feature["geometry"]["coordinates"]

        properties = feature.get("properties", {})

        return {
            "name": properties.get(
                "full_address"
            ) or properties.get(
                "name"
            ) or query,
            "coordinates": coordinates,
        }

    except requests.RequestException as exc:
        logger.exception(
            "Mapbox geocoding request failed"
        )
        raise GeocodingError(
            "Unable to geocode location."
        ) from exc
