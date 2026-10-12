
from datetime import datetime, timezone

from django.test import SimpleTestCase

from .services.checkpoint_service import (
    METERS_PER_MILE,
    generate_checkpoints,
)


class CheckpointTests(SimpleTestCase):

    def setUp(self):
        self.departure = datetime(
            2026, 10, 15, 8, 0,
            tzinfo=timezone.utc,
        )

        # Simplified 100-mile test route.
        self.route = {
            "id": "route_1",
            "distance_meters": 100 * METERS_PER_MILE,
            "duration_seconds": 7200,
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-87.9, 41.8],
                    [-87.5, 41.8],
                    [-87.0, 41.8],
                ],
            },
        }

    def test_25_mile_checkpoints(self):
        points = generate_checkpoints(
            self.route, self.departure, 25
        )

        self.assertEqual(len(points), 5)
        self.assertEqual(
            [p["mile_marker"] for p in points],
            [0, 25, 50, 75, 100],
        )

    def test_10_mile_checkpoints(self):
        points = generate_checkpoints(
            self.route, self.departure, 10
        )
        self.assertEqual(len(points), 11)

    def test_50_mile_checkpoints(self):
        points = generate_checkpoints(
            self.route, self.departure, 50
        )
        self.assertEqual(len(points), 3)

    def test_eta_increases(self):
        points = generate_checkpoints(
            self.route, self.departure, 25
        )

        self.assertLess(
            points[0]["eta"],
            points[-1]["eta"],
        )

        self.assertEqual(
            points[-1]["elapsed_minutes"],
            120,
        )

    def test_distance_coverage(self):
        points = generate_checkpoints(
            self.route, self.departure, 25
        )

        covered = sum(
            point["represented_miles"]
            for point in points
        )

        self.assertAlmostEqual(
            covered, 100, places=2
        )

    def test_invalid_interval(self):
        with self.assertRaises(ValueError):
            generate_checkpoints(
                self.route, self.departure, 15
            )
