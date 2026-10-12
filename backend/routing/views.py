
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import RouteRequestSerializer
from .services.geocoding_service import (
    GeocodingError,
    geocode_location,
)
from .services.routing_service import (
    RoutingError,
    get_routes,
)
from .services.mapbox_service import (
    MapboxRoutingError,
    get_mapbox_routes,
)
from .services.checkpoint_service import generate_checkpoints
from .services.weather_service import (
    WeatherServiceError,
    fetch_checkpoint_weather,
)
from .services.risk_service import calculate_risk
from .services.recommendation_service import (
    summarize_route,
    recommend_best_route,
)

from datetime import datetime, timedelta, timezone

from .serializers import CorridorForecastSerializer
from .services.corridor_service import (
    CorridorForecastError,
    get_corridor_forecast,
)

@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "ok",
        "service": "Spotter Weather Routing API",
        "version": "1.0.0",
    })

@api_view(["GET"])
def geocode_search(request):
    query = request.query_params.get("q", "").strip()

    if not 2 <= len(query) <= 255:
        return Response(
            {"error": "Query must contain 2–255 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        location = geocode_location(query)
        return Response(location)

    except GeocodingError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

@api_view(["POST"])
def calculate_routes(request):
    serializer = RouteRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data

    try:
        origin = geocode_location(data["origin"])
        destination = geocode_location(data["destination"])

        result = get_mapbox_routes(
            origin["coordinates"],
            destination["coordinates"],
        )

        routes = result["routes"]

        # Step 1: Generate distance-based checkpoints.
        all_checkpoints = []

        for route in routes:
            checkpoints = generate_checkpoints(
                route=route,
                departure_time=data["departure_time"],
                interval_miles=int(data["checkpoint_interval"]),
            )

            route["checkpoints"] = checkpoints
            route["checkpoint_count"] = len(checkpoints)

            all_checkpoints.extend(checkpoints)

        # Step 2: Fetch ETA-specific weather in batches.
        weather_results = fetch_checkpoint_weather(
            all_checkpoints
        )

        # Step 3: Apply forecast and load-based risk.
        for checkpoint, weather in zip(
            all_checkpoints,
            weather_results,
        ):
            checkpoint["weather"] = weather

            if weather is None:
                checkpoint["risk"] = calculate_risk(
                    None, None, None,
                    data["load_weight"],
                )
            else:
                checkpoint["risk"] = calculate_risk(
                    wind_mph=weather["wind_mph"],
                    rain_in_hr=weather["rain_in_hr"],
                    snow_in_hr=weather["snow_in_hr"],
                    load_weight=data["load_weight"],
                )

        # Step 4: Calculate route risk summaries.
        for route in routes:
            route["risk_summary"] = summarize_route(route)

        # Step 5: Select the best eligible route.
        recommendation = recommend_best_route(routes)

        return Response({
            "origin": origin,
            "destination": destination,
            "departure_time": (
                data["departure_time"].isoformat()
            ),
            "load_weight": data["load_weight"],
            "checkpoint_interval": int(
                data["checkpoint_interval"]
            ),
            "routing_provider": "mapbox",
            "weather_provider": "open-meteo",
            **result,
            **recommendation,
        })

    except (GeocodingError, MapboxRoutingError) as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    except WeatherServiceError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    except ValueError:
        return Response(
            {"error": "Invalid route or weather data."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

@api_view(["POST"])
def corridor_forecast(request):
    serializer = CorridorForecastSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data

    # Forecast slider starts at the next UTC hour.
    now = datetime.now(timezone.utc)

    reference_time = now.replace(
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(hours=1)

    try:
        result = get_corridor_forecast(
            coordinates=data["coordinates"],
            reference_time=reference_time,
            load_weight=data["load_weight"],
        )

        return Response(result)

    except CorridorForecastError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )
