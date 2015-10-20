from rest_framework import serializers
from prices import Price
from django.conf import settings


class PriceField(serializers.Field):
    def to_representation(self, value):
        return value.net

    def to_internal_value(self, data):
        if isinstance(data, Price):
            return data
        if data is None:
            data = '0.0'
        return Price(net=data, currency=settings.DEFAULT_CURRENCY)
