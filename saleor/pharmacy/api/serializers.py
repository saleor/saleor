from rest_framework import serializers

from ..pharmacy.models import Patient


class HealthProfileSerializer(serializers.ModelSerializer):
    self_href = serializers.HyperlinkedIdentityField(
        view_name="patient-detail", read_only=True, lookup_field="uuid"
    )

    class Meta:
        model = Patient
        exclude = ("id", "home_address")
