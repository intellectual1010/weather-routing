
from django.test import SimpleTestCase

from .services.recommendation_service import (
    recommend_best_route,
    summarize_route,
)


def make_checkpoint(level, miles):
    scores = {
        "low": 0,
        "moderate": 1,
        "high": 2,
        "severe": 3,
        "no_travel": 4,
    }

    return {
        "represented_miles": miles,
        "risk": {
            "level": level,
            "score": scores.get(level),
        },
    }


class RecommendationTests(SimpleTestCase):

    def make_route(self, route_id, checkpoints, duration):
        route = {
            "id": route_id,
            "duration_seconds": duration,
            "checkpoints": checkpoints,
        }

        route["risk_summary"] = summarize_route(route)
        return route

    def test_fewest_severe_miles_wins(self):
        a = self.make_route("a", [
            make_checkpoint("severe", 20),
            make_checkpoint("low", 80),
        ], 36000)

        b = self.make_route("b", [
            make_checkpoint("high", 50),
            make_checkpoint("low", 50),
        ], 40000)

        result = recommend_best_route([a, b])
        self.assertEqual(
            result["recommended_route_id"], "b"
        )

    def test_fewest_high_miles_wins(self):
        a = self.make_route("a", [
            make_checkpoint("high", 60),
            make_checkpoint("low", 40),
        ], 30000)

        b = self.make_route("b", [
            make_checkpoint("high", 20),
            make_checkpoint("low", 80),
        ], 38000)

        result = recommend_best_route([a, b])
        self.assertEqual(
            result["recommended_route_id"], "b"
        )

    def test_no_travel_excluded(self):
        a = self.make_route("a", [
            make_checkpoint("no_travel", 20),
            make_checkpoint("low", 80),
        ], 30000)

        b = self.make_route("b", [
            make_checkpoint("moderate", 100),
        ], 36000)

        result = recommend_best_route([a, b])
        self.assertEqual(
            result["recommended_route_id"], "b"
        )

    def test_unknown_data_not_recommended(self):
        a = self.make_route("a", [
            make_checkpoint("unknown", 100),
        ], 30000)

        result = recommend_best_route([a])
        self.assertIsNone(result["recommended_route_id"])
