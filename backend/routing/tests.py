
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient


class RoutingAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")

    def test_missing_required_fields(self):
        response = self.client.post(
            "/api/routes/",
            {"origin": "Chicago"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_same_origin_destination(self):
        response = self.client.post(
            "/api/routes/",
            {
                "origin": "Chicago",
                "destination": "Chicago",
                "departure_time": "2026-10-15T08:00:00Z",
                "load_weight": 35000,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("routing.views.fetch_checkpoint_weather")
    @patch("routing.views.get_mapbox_routes")
    @patch("routing.views.geocode_location")
    def test_route_endpoint(
        self,
        mock_geocode,
        mock_routes,
        mock_weather,
    ):
        # Keep your existing origin/destination mock data.

        mock_geocode.side_effect = [
            {
                "name": "Chicago",
                "coordinates": [-87.62, 41.88],
            },
            {
                "name": "Atlanta",
                "coordinates": [-84.39, 33.75],
            },
        ]

        mock_routes.return_value = {
            "routes": [],
            "route_count": 0,
            "has_three_routes": False,
            "message": "Mock test",
        }

        mock_weather.return_value = []

        response = self.client.post(
            "/api/routes/",
            {
                "origin": "Chicago",
                "destination": "Atlanta",
                "departure_time": "2026-10-15T08:00:00Z",
                "load_weight": 35000,
                "checkpoint_interval": 25,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("recommended_route_id", response.data)
