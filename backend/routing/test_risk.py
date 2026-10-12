
from django.test import SimpleTestCase

from .services.risk_service import (
    calculate_risk,
    classify_rain,
    classify_snow,
    classify_wind,
)


class WeatherRiskTests(SimpleTestCase):

    def risk(self, wind=0, rain=0, snow=0, load=10000):
        return calculate_risk(
            wind_mph=wind,
            rain_in_hr=rain,
            snow_in_hr=snow,
            load_weight=load,
        )["level"]

    def test_wind_thresholds(self):
        self.assertEqual(classify_wind(24.99), "low")
        self.assertEqual(classify_wind(25), "moderate")
        self.assertEqual(classify_wind(35), "high")
        self.assertEqual(classify_wind(45), "severe")
        self.assertEqual(classify_wind(55), "no_travel")

    def test_rain_thresholds(self):
        self.assertEqual(classify_rain(0.09), "low")
        self.assertEqual(classify_rain(0.10), "moderate")
        self.assertEqual(classify_rain(0.25), "high")
        self.assertEqual(classify_rain(0.50), "severe")
        self.assertEqual(classify_rain(1.00), "severe")
        self.assertEqual(classify_rain(1.01), "no_travel")

    def test_snow_thresholds(self):
        self.assertEqual(classify_snow(0.49), "low")
        self.assertEqual(classify_snow(0.5), "moderate")
        self.assertEqual(classify_snow(1.0), "high")
        self.assertEqual(classify_snow(2.0), "severe")
        self.assertEqual(classify_snow(3.0), "severe")
        self.assertEqual(classify_snow(3.01), "no_travel")

    def test_wind_no_travel_for_any_load(self):
        self.assertEqual(
            self.risk(wind=55, load=10000),
            "no_travel",
        )

    def test_heavy_load_no_travel(self):
        self.assertEqual(
            self.risk(wind=50, load=35000),
            "no_travel",
        )

    def test_heavy_load_severe(self):
        self.assertEqual(
            self.risk(wind=38, load=45000),
            "severe",
        )

    def test_exact_load_boundary(self):
        self.assertEqual(
            self.risk(wind=50, load=30000),
            "severe",
        )
        self.assertEqual(
            self.risk(wind=38, load=40000),
            "high",
        )

    def test_highest_weather_risk_wins(self):
        self.assertEqual(
            self.risk(wind=10, rain=0.70, snow=0),
            "severe",
        )

    def test_missing_forecast(self):
        self.assertEqual(
            self.risk(wind=None),
            "unknown",
        )
