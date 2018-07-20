from django.core.serializers.json import (
    DjangoJSONEncoder, Serializer as JsonSerializer)
from prices import Money


class Serializer(JsonSerializer):
    def _init_options(self):
        super()._init_options()
        self.json_kwargs['cls'] = CustomJsonEncoder


class CustomJsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Money):
            return "{} {}".format(obj.amount, obj.currency)
        return super().default(obj)
