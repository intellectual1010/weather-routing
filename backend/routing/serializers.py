
from rest_framework import serializers


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
