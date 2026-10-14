
from unittest.mock import patch
from django.test import SimpleTestCase

from .services.weather_sampling_service import (
    select_weather_locations,
    fetch_sampled_weather,
)


class WeatherSamplingTests(SimpleTestCase):

    def setUp(self):
        self.checkpoints = [
            {
                "latitude": 40 + i * 0.2,
                "longitude": -110 + i * 0.2,
                "eta": "2026-10-15T12:00:00+00:00",
            }
            for i in range(100)
        ]

    def test_location_limit(self):
        locations = select_weather_locations(
            self.checkpoints,
            max_locations=35,
        )

        self.assertLessEqual(len(locations), 35)

    def test_empty_checkpoints(self):
        self.assertEqual(
            fetch_sampled_weather([]), []
        )

    @patch(
        "routing.services.weather_sampling_service."
        "select_forecast"
    )
    @patch(
        "routing.services.weather_sampling_service."
        "fetch_location_forecast"
    )
    def test_all_checkpoints_preserved(
        self,
        mock_fetch,
        mock_select,
    ):
        mock_fetch.return_value = {"forecast": {}}
        mock_select.return_value = {
            "wind_mph": 10,
            "rain_in_hr": 0,
            "snow_in_hr": 0,
            "forecast_time": "2026-10-15T12:00:00+00:00",
            "source": "weatherapi",
        }

        with self.settings(
            WEATHER_MAX_WORKERS=3,
            WEATHER_MAX_SAMPLE_DISTANCE_KM=10000,
        ):
            results = fetch_sampled_weather(
                self.checkpoints,
                max_locations=20,
            )

        self.assertEqual(
            len(results),
            len(self.checkpoints),
        )
        self.assertLessEqual(
            mock_fetch.call_count,
            20,
        )

    @patch(
        "routing.services.weather_sampling_service."
        "fetch_location_forecast"
    )
    def test_distant_forecast_not_used(
        self,
        mock_fetch,
    ):
        mock_fetch.return_value = {"forecast": {}}

        checkpoints = [
            {
                "latitude": 40.0,
                "longitude": -110.0,
                "eta": "2026-10-15T12:00:00Z",
            },
            {
                "latitude": 48.0,
                "longitude": -120.0,
                "eta": "2026-10-15T12:00:00Z",
            },
        ]

        with self.settings(
            WEATHER_MAX_WORKERS=2,
            WEATHER_MAX_SAMPLE_DISTANCE_KM=10,
        ):
            results = fetch_sampled_weather(
                checkpoints,
                max_locations=1,
            )

        self.assertIsNone(results[1])
