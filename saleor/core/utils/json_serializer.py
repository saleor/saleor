from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.json import Serializer as JsonSerializer
from draftjs_sanitizer import SafeJSONEncoder
from measurement.measures import Weight
from prices import Money

MONEY_TYPE = "Money"


class Serializer(JsonSerializer):
    def _init_options(self):
        super()._init_options()
        self.json_kwargs["cls"] = CustomJsonEncoder


class CustomJsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Money):
            return {"_type": MONEY_TYPE, "amount": obj.amount, "currency": obj.currency}
        # Mirror implementation of django_measurement.MeasurementField.value_to_string
        if isinstance(obj, Weight):
            return "%s:%s" % (obj.value, obj.unit)
        return super().default(obj)


class HTMLSafeJSON(SafeJSONEncoder, DjangoJSONEncoder):
    """Escape dangerous characters from JSON.

    It is used for integrating JSON into HTML content in addition to
    serializing Django objects.
    """
