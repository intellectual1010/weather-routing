
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

        result = get_routes(
            origin["coordinates"],
            destination["coordinates"],
        )

        return Response({
            "origin": origin,
            "destination": destination,
            "departure_time": data["departure_time"].isoformat(),
            "load_weight": data["load_weight"],
            "checkpoint_interval": data["checkpoint_interval"],
            **result,
        })

    except (GeocodingError, RoutingError) as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )
