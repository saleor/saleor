from collections import OrderedDict

import graphene
from django.core.serializers.json import Serializer


class WebhookSerializer(Serializer):
    def __init__(self):
        super().__init__()
        self.additional_fields = {}

    def serialize(
        self,
        queryset,
        *,
        stream=None,
        fields=None,
        use_natural_foreign_keys=False,
        use_natural_primary_keys=False,
        progress_output=None,
        object_count=0,
        **options,
    ):
        self.additional_fields = options.pop("additional_fields", {})
        return super().serialize(
            queryset,
            stream=None,
            fields=None,
            use_natural_foreign_keys=False,
            use_natural_primary_keys=False,
            progress_output=None,
            object_count=0,
            **options,
        )

    def get_dump_object(self, obj):
        obj_id = graphene.Node.to_global_id(obj._meta.object_name, obj.id)
        data = OrderedDict([("type", str(obj._meta.object_name)), ("id", obj_id)])
        if not self.use_natural_primary_keys or not hasattr(obj, "natural_key"):
            data["id"] = self._value_from_field(obj, obj._meta.pk)
        data.update(self._current)
        data.update(self.additional_fields)
        return data
