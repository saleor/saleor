from rest_framework import serializers

from ...pharmacy.models import Patient
from ...account.models import Address


class AddressSerializer(serializers.ModelSerializer):
    # remap fields to match what the frontend expects
    lineOne = serializers.CharField(source="street_address_1")
    lineTwo = serializers.CharField(source="street_address_2")
    city = serializers.CharField()
    zip = serializers.CharField(source="postal_code")
    state = serializers.CharField(source="country_area")

    class Meta:
        model = Address
        exclude = (
            "id",
            "first_name",
            "last_name",
            "company_name",
            "country",
            "country_area",
            "phone",
            "private_metadata",
            "metadata",
            "postal_code",
            "city_area",
            "street_address_1",
            "street_address_2",
        )


class HealthProfileSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="customer.first_name")
    lastName = serializers.CharField(source="customer.last_name")
    # add middle initial onto Patient?
    # middleInitial = serializers.CharField(source="customer.middle_name")
    dateOfBirth = serializers.DateField(source="date_of_birth")
    gender = serializers.CharField(source="gender_assigned_at_birth")
    email = serializers.CharField(source="customer.email")
    phoneNumber = serializers.CharField(source="customer.default_billing_address.phone")
    address = AddressSerializer(source="customer.default_billing_address")
    isDefault = serializers.BooleanField(default=True)

    class Meta:
        model = Patient
        exclude = ("id", "customer", "date_of_birth", "gender_assigned_at_birth")
