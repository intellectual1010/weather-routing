
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import SimpleTestCase

from .services.weather_service import (
    fetch_location_forecast,
)


class WeatherCacheTests(SimpleTestCase):

    def setUp(self):
        cache.clear()

    @patch(
        "routing.services.weather_service.requests.get"
    )
    def test_forecast_uses_cache(self, mock_get):
        mock_response = Mock()

        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "forecast": {
                "forecastday": [
                    {"date": "2026-10-15", "hour": []}
                ]
            }
        }

        mock_get.return_value = mock_response

        with self.settings(
            WEATHERAPI_KEY="test_key"
        ):
            first = fetch_location_forecast(
                41.8781, -87.6298
            )

            second = fetch_location_forecast(
                41.8781, -87.6298
            )

        self.assertEqual(first, second)
        mock_get.assert_called_once()
