import json

from django.core.serializers.base import DeserializationError
from django.core.serializers.json import (
    DjangoJSONEncoder, PythonDeserializer, Serializer as JsonSerializer)
from prices import Money

MONEY_TYPE = 'Money'


class Serializer(JsonSerializer):
    def _init_options(self):
        super()._init_options()
        self.json_kwargs['cls'] = CustomJsonEncoder


class CustomJsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Money):
            return {
                '_type': MONEY_TYPE, 'amount': obj.amount,
                'currency': obj.currency}
        return super().default(obj)


def object_hook(obj):
    if '_type' in obj and obj['_type'] == MONEY_TYPE:
        return Money(obj['amount'], obj['currency'])
    return obj


def Deserializer(stream_or_string, **options):
    """Deserialize a stream or string of JSON data. This is a slightly modified
    copy of Django implementation with additional argument <object_hook> in
    json.loads"""
    if not isinstance(stream_or_string, (bytes, str)):
        stream_or_string = stream_or_string.read()
    if isinstance(stream_or_string, bytes):
        stream_or_string = stream_or_string.decode()
    try:
        objects = json.loads(stream_or_string, object_hook=object_hook)
        yield from PythonDeserializer(objects, **options)
    except Exception as exc:
        # ugly construction to overcome pylint's warning
        # "The except handler raises immediately"
        if isinstance(exc, (GeneratorExit, DeserializationError)):
            raise
        raise DeserializationError() from exc
