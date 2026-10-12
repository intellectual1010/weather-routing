
from django.test import SimpleTestCase
from rest_framework.test import APIClient

from .services.corridor_service import (
    CorridorForecastError,
    sample_corridor,
)


class CorridorTests(SimpleTestCase):

    def test_sample_count(self):
        coordinates = [
            [-87.6298, 41.8781],
            [-86.1581, 39.7684],
            [-84.3880, 33.7490],
        ]

        points = sample_corridor(coordinates)

        self.assertEqual(len(points), 35)
        self.assertEqual(points[0]["progress_percent"], 0)
        self.assertEqual(points[-1]["progress_percent"], 100)

        self.assertAlmostEqual(
            points[0]["longitude"],
            coordinates[0][0],
            places=4,
        )

        self.assertAlmostEqual(
            points[-1]["latitude"],
            coordinates[-1][1],
            places=4,
        )

    def test_invalid_geometry(self):
        with self.assertRaises(CorridorForecastError):
            sample_corridor([[-87.62, 41.88]])

    def test_invalid_api_coordinates(self):
        client = APIClient()

        response = client.post(
            "/api/weather/corridor/",
            {
                "coordinates": [
                    [-200, 41],
                    [-84, 33],
                ],
                "load_weight": 42000,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
