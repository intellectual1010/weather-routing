
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase

from .services.weather_service import fetch_weather_batch


class WeatherCacheTests(SimpleTestCase):

    def setUp(self):
        cache.clear()

    @patch(
        "routing.services.weather_service."
        "_fetch_weather_batch_uncached"
    )
    def test_repeated_batch_uses_cache(self, mock_fetch):
        mock_fetch.return_value = [
            {"wind_mph": 12.0}
        ]

        points = [{
            "latitude": 41.8781,
            "longitude": -87.6298,
            "eta": "2026-10-15T10:00:00+00:00",
        }]

        first = fetch_weather_batch(points)
        second = fetch_weather_batch(points)

        self.assertEqual(first, second)
        mock_fetch.assert_called_once()
