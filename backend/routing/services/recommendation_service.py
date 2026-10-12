
from .risk_service import RISK_SCORES

LEVELS = (
    "low",
    "moderate",
    "high",
    "severe",
    "no_travel",
)


def summarize_route(route):
    """Summarize checkpoint risks into approximate road miles."""

    totals = {level: 0.0 for level in LEVELS}
    unknown_miles = 0.0

    weighted_total = 0.0
    known_miles = 0.0

    for checkpoint in route["checkpoints"]:
        risk = checkpoint["risk"]
        miles = checkpoint["represented_miles"]
        level = risk["level"]

        if level == "unknown":
            unknown_miles += miles
            continue

        totals[level] += miles
        weighted_total += RISK_SCORES[level] * miles
        known_miles += miles

    average = (
        weighted_total / known_miles
        if known_miles > 0
        else None
    )

    highest_level = max(
        (
            level for level in LEVELS
            if totals[level] > 0
        ),
        key=lambda level: RISK_SCORES[level],
        default="unknown",
    )

    summary = {
        f"{level}_miles": round(totals[level], 2)
        for level in LEVELS
    }

    summary.update({
        "unknown_miles": round(unknown_miles, 2),
        "average_risk": (
            round(average, 3)
            if average is not None else None
        ),
        "highest_risk": highest_level,
        "forecast_complete": unknown_miles == 0,
        "safe_to_recommend": (
            unknown_miles == 0
            and totals["no_travel"] == 0
        ),
    })

    return summary


def recommend_best_route(routes):
    """
    Rank routes using the assessment's priorities.

    First exclude routes with unknown or No Travel
    conditions from a positive recommendation.
    """

    candidates = [
        route for route in routes
        if route["risk_summary"]["safe_to_recommend"]
    ]

    if not candidates:
        return {
            "recommended_route_id": None,
            "recommendation_status": "no_safe_route",
            "recommendation_reason": (
                "No route can be recommended because "
                "all available routes contain No Travel "
                "conditions or incomplete forecasts."
            ),
        }

    def ranking_key(route):
        risk = route["risk_summary"]

        return (
            risk["severe_miles"],
            risk["high_miles"],
            risk["average_risk"],
            route["duration_seconds"],
        )

    winner = min(candidates, key=ranking_key)

    return {
        "recommended_route_id": winner["id"],
        "recommendation_status": "available",
        "recommendation_reason": (
            "Selected by fewest Severe miles, "
            "fewest High miles, lowest average risk, "
            "then shortest travel time."
        ),
    }
