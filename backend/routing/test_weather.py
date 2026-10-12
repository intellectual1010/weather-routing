
from django.test import SimpleTestCase
from .services.weather_service import select_forecast


class WeatherForecastTests(SimpleTestCase):

    def setUp(self):
        self.data = {
            "hourly": {
                "time": [
                    "2026-10-15T08:00",
                    "2026-10-15T09:00",
                    "2026-10-15T10:00",
                ],
                "wind_speed_10m": [15, 38, 55],
                "rain": [0.0, 0.25, 0.0],
                "snowfall": [0.0, 2.54, 0.0],
            }
        }

    def test_select_nearest_hour(self):
        result = select_forecast(
            self.data,
            "2026-10-15T09:10:00+00:00",
        )

        self.assertEqual(result["wind_mph"], 38)
        self.assertEqual(result["rain_in_hr"], 0.25)
        self.assertAlmostEqual(
            result["snow_in_hr"],
            1.0,
        )

    def test_timezone_conversion(self):
        result = select_forecast(
            self.data,
            "2026-10-15T04:10:00-05:00",
        )

        self.assertEqual(result["wind_mph"], 38)

    def test_missing_forecast(self):
        result = select_forecast(
            self.data,
            "2026-10-17T09:00:00+00:00",
        )

        self.assertIsNone(result)
