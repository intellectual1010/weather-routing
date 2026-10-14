
from datetime import datetime, timezone
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase

from .services.weather_service import (
    select_forecast,
    fetch_checkpoint_weather,
)


def sample_weatherapi_response():
    return {
        "forecast": {
            "forecastday": [
                {
                    "date": "2026-10-15",
                    "hour": [
                        {
                            "time_epoch": 1792051200,
                            "wind_mph": 15,
                            "precip_in": 0,
                            "snow_cm": 0,
                        },
                        {
                            "time_epoch": 1792054800,
                            "wind_mph": 38,
                            "precip_in": 0.25,
                            "snow_cm": 2.54,
                        },
                    ],
                }
            ]
        }
    }


class WeatherForecastTests(SimpleTestCase):

    def setUp(self):
        cache.clear()
        self.data = sample_weatherapi_response()

    def test_nearest_hour(self):
        eta = datetime.fromtimestamp(
            1792054800 + 600,
            tz=timezone.utc,
        )

        result = select_forecast(self.data, eta)

        self.assertIsNotNone(result)
        self.assertEqual(result["wind_mph"], 38)
        self.assertEqual(result["rain_in_hr"], 0.25)
        self.assertAlmostEqual(result["snow_in_hr"], 1.0)

    def test_missing_forecast(self):
        result = select_forecast(
            self.data,
            "2026-10-20T12:00:00+00:00",
        )

        self.assertIsNone(result)

    def test_missing_snow_data(self):
        data = sample_weatherapi_response()

        data["forecast"]["forecastday"][0]["hour"][1][
            "snow_cm"
        ] = None

        eta = datetime.fromtimestamp(
            1792054800,
            tz=timezone.utc,
        )

        self.assertIsNone(select_forecast(data, eta))

    @patch(
        "routing.services.weather_service."
        "fetch_location_forecast"
    )
    def test_checkpoint_result_count(self, mock_fetch):
        mock_fetch.return_value = self.data

        eta = datetime.fromtimestamp(
            1792054800,
            tz=timezone.utc,
        ).isoformat()

        checkpoints = [
            {
                "latitude": 41.8781,
                "longitude": -87.6298,
                "eta": eta,
            },
            {
                "latitude": 39.7684,
                "longitude": -86.1581,
                "eta": eta,
            },
        ]

        results = fetch_checkpoint_weather(
            checkpoints
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(
            all(item is not None for item in results)
        )
