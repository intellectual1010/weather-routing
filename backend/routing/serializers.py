
from rest_framework import serializers
from datetime import datetime

class RouteRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
    )
    destination = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
    )
    departure_time = serializers.DateTimeField()
    load_weight = serializers.IntegerField(
        min_value=0,
        max_value=100000,
    )
    checkpoint_interval = serializers.ChoiceField(
        choices=[10, 25, 50],
        default=25,
    )

    def validate(self, attrs):
        if (
            attrs["origin"].strip().lower()
            == attrs["destination"].strip().lower()
        ):
            raise serializers.ValidationError(
                "Origin and destination must be different."
            )

        return attrs
    
    def validate_departure_time(self, value):
        raw = self.initial_data.get("departure_time", "")

        if isinstance(raw, str):
            text = raw.strip()

            # Require Z or an explicit UTC offset.
            has_timezone = (
                text.endswith("Z")
                or (
                    len(text) >= 6
                    and text[-6] in ("+", "-")
                    and text[-3] == ":"
                )
            )

            if not has_timezone:
                raise serializers.ValidationError(
                    "Departure time must include a timezone offset."
                )

        if value.tzinfo is None:
            raise serializers.ValidationError(
                "Timezone-aware departure time is required."
            )

        return value

class CorridorPointSerializer(serializers.ListField):
    child = serializers.FloatField()
    min_length = 2
    max_length = 2


class CorridorForecastSerializer(serializers.Serializer):
    coordinates = serializers.ListField(
        child=CorridorPointSerializer(),
        min_length=2,
        max_length=10000,
    )
    load_weight = serializers.IntegerField(
        min_value=0,
        max_value=100000,
    )

    def validate_coordinates(self, coordinates):
        for longitude, latitude in coordinates:
            if not (-180 <= longitude <= 180):
                raise serializers.ValidationError(
                    "Invalid longitude."
                )
            if not (-90 <= latitude <= 90):
                raise serializers.ValidationError(
                    "Invalid latitude."
                )
        return coordinates
