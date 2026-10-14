
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

import hashlib
import json
import logging
import time
import os

from django.core.cache import cache
from .services.weather_service import _cache_key
from .services.weather_sampling_service import fetch_sampled_weather

logger = logging.getLogger(__name__)

@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "ok",
        "service": "Weather Routing API",
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

    # Cache identical trip-analysis requests.
    # Changing departure time, load or checkpoint interval
    # creates a different cache key.
    cache_parameters = {
        "origin": data["origin"].strip().lower(),
        "destination": data["destination"].strip().lower(),
        "departure_time": data["departure_time"].isoformat(),
        "load_weight": data["load_weight"],
        "checkpoint_interval": int(data["checkpoint_interval"]),
    }

    cache_digest = hashlib.sha256(
        json.dumps(
            cache_parameters,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    route_cache_key = f"route-analysis:v2:{cache_digest}"

    cached_result = cache.get(route_cache_key)

    logger.info(
        "Route request worker=%s cache_hit=%s",
        os.getpid(),
        cached_result is not None,
    )

    if cached_result is not None:
        logger.info("Route analysis cache hit")
        return Response(cached_result)

    analysis_started = time.perf_counter()

    try:
        step_started = time.perf_counter()
        
        origin = geocode_location(data["origin"])
        destination = geocode_location(data["destination"])

        logger.info(
            "PERF geocoding: %.2fs",
            time.perf_counter() - step_started,
        )

        step_started = time.perf_counter()

        result = get_mapbox_routes(
            origin_coords=origin["coordinates"],
            destination_coords=destination["coordinates"],
            origin_name=data["origin"],
            destination_name=data["destination"],
        )

        logger.info(
            "PERF Mapbox: %.2fs",
            time.perf_counter() - step_started,
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
        step_started = time.perf_counter()
        
        unique_cells = {
            _cache_key(point["latitude"], point["longitude"])
            for point in all_checkpoints
        }

        logger.info(
            "WEATHER GRID: %d checkpoints -> %d unique forecast cells",
            len(all_checkpoints),
            len(unique_cells),
        )
        
        weather_results = fetch_sampled_weather(
            all_checkpoints
        )

        logger.info(
            "PERF WeatherAPI: %.2fs for %d checkpoints",
            time.perf_counter() - step_started,
            len(all_checkpoints),
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

        response_data = {
            "origin": origin,
            "destination": destination,
            "departure_time": data["departure_time"].isoformat(),
            "load_weight": data["load_weight"],
            "checkpoint_interval": int(
                data["checkpoint_interval"]
            ),
            "routing_provider": "mapbox",
            "weather_provider": "weatherapi",
            **result,
            **recommendation,
        }

        cache.set(
            route_cache_key,
            response_data,
            timeout=600,
        )

        logger.info(
            "Route analysis completed in %.2fs",
            time.perf_counter() - analysis_started,
        )

        return Response(response_data)

        return Response(response_data)

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
