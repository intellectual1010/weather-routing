
from decimal import Decimal

RISK_SCORES = {
    "low": 0,
    "moderate": 1,
    "high": 2,
    "severe": 3,
    "no_travel": 4,
}


def classify_wind(wind_mph):
    if wind_mph >= 55:
        return "no_travel"
    if wind_mph >= 45:
        return "severe"
    if wind_mph >= 35:
        return "high"
    if wind_mph >= 25:
        return "moderate"
    return "low"


def classify_rain(rain_in_hr):
    if rain_in_hr > 1.00:
        return "no_travel"
    if rain_in_hr >= 0.50:
        return "severe"
    if rain_in_hr >= 0.25:
        return "high"
    if rain_in_hr >= 0.10:
        return "moderate"
    return "low"


def classify_snow(snow_in_hr):
    if snow_in_hr > 3.0:
        return "no_travel"
    if snow_in_hr >= 2.0:
        return "severe"
    if snow_in_hr >= 1.0:
        return "high"
    if snow_in_hr >= 0.5:
        return "moderate"
    return "low"


def calculate_risk(
    wind_mph,
    rain_in_hr,
    snow_in_hr,
    load_weight,
):
    """Classify a checkpoint using weather and load rules."""

    values = (
        wind_mph,
        rain_in_hr,
        snow_in_hr,
    )

    if any(value is None for value in values):
        return {
            "level": "unknown",
            "score": None,
            "reason": "Weather forecast unavailable",
            "factors": {},
        }

    wind = float(wind_mph)
    rain = float(rain_in_hr)
    snow = float(snow_in_hr)

    if (
        not all(
            __import__("math").isfinite(v)
            for v in (wind, rain, snow)
        )
        or any(v < 0 for v in (wind, rain, snow))
    ):
        raise ValueError("Invalid weather readings")

    factors = {
        "wind": classify_wind(wind),
        "rain": classify_rain(rain),
        "snow": classify_snow(snow),
    }

    reasons = []

    # Load-specific overrides.
    if wind >= 55:
        factors["wind"] = "no_travel"
        reasons.append("Wind is at least 55 mph")

    elif wind >= 45 and load_weight > 30000:
        factors["wind"] = "no_travel"
        reasons.append(
            "Wind is at least 45 mph with load above 30,000 lb"
        )

    elif wind >= 35 and load_weight > 40000:
        factors["wind"] = "severe"
        reasons.append(
            "Wind is at least 35 mph with load above 40,000 lb"
        )

    level = max(
        factors.values(),
        key=lambda name: RISK_SCORES[name],
    )

    if not reasons:
        leading = [
            name
            for name, risk in factors.items()
            if risk == level
        ]
        reasons.append(
            f"{', '.join(leading).title()} risk: "
            f"{level.replace('_', ' ').title()}"
        )

    return {
        "level": level,
        "score": RISK_SCORES[level],
        "reason": "; ".join(reasons),
        "factors": factors,
    }
