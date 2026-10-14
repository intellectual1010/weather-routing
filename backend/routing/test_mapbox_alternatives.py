
from unittest.mock import patch

from django.test import SimpleTestCase

from .services.mapbox_service import (
    get_candidate_waypoints,
    get_mapbox_routes,
    is_distinct_route,
)


def make_route(distance, latitude):
    return {
        "distance": distance,
        "duration": distance / 22,
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [-120, latitude],
                [-115, latitude],
                [-110, latitude],
            ],
        },
    }


class MapboxAlternativeTests(SimpleTestCase):

    def test_candidate_city_selection(self):
        candidates = get_candidate_waypoints(
            "Seattle, Washington",
            "Phoenix, Arizona",
        )

        self.assertIn(
            "Sacramento, California",
            candidates,
        )

    def test_reverse_direction(self):
        candidates = get_candidate_waypoints(
            "Phoenix, Arizona",
            "Seattle, Washington",
        )

        self.assertGreater(len(candidates), 0)

    def test_distinct_geometry(self):
        a = {
            "geometry": make_route(
                1000000, 35
            )["geometry"],
        }

        b = {
            "geometry": make_route(
                1100000, 40
            )["geometry"],
        }

        self.assertTrue(
            is_distinct_route(b, [a])
        )

    def test_duplicate_geometry_rejected(self):
        a = {
            "geometry": make_route(
                1000000, 35
            )["geometry"],
        }

        self.assertFalse(
            is_distinct_route(a, [a])
        )

    @patch(
        "routing.services.mapbox_service."
        "geocode_location"
    )
    @patch(
        "routing.services.mapbox_service."
        "request_mapbox_directions"
    )
    def test_three_routes_generated(
        self,
        mock_directions,
        mock_geocode,
    ):
        primary = make_route(1000000, 35)
        alternative = make_route(1100000, 38)
        waypoint_route = make_route(1200000, 41)

        mock_directions.side_effect = [
            [primary, alternative],
            [waypoint_route],
        ]

        mock_geocode.return_value = {
            "name": "Sacramento",
            "coordinates": [-121.49, 38.58],
        }

        result = get_mapbox_routes(
            origin_coords=[-122.33, 47.60],
            destination_coords=[-112.07, 33.45],
            origin_name="Seattle, Washington",
            destination_name="Phoenix, Arizona",
        )

        self.assertEqual(result["route_count"], 3)
        self.assertTrue(result["has_three_routes"])

        self.assertEqual(
            [route["id"] for route in result["routes"]],
            ["route_1", "route_2", "route_3"],
        )

        self.assertEqual(
            result["routes"][2]["via_city"],
            "Sacramento, California",
        )
