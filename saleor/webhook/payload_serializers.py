from collections import OrderedDict
from collections.abc import Iterable

import graphene
from django.core.serializers.json import Serializer as JSONSerializer
from django.core.serializers.python import Serializer as PythonBaseSerializer


class PythonSerializer(PythonBaseSerializer):
    def get_dump_object(self, obj):
        obj_id = graphene.Node.to_global_id(obj._meta.object_name, obj.id)
        data = OrderedDict([("type", str(obj._meta.object_name)), ("id", obj_id)])
        data.update(self._current)
        return data


class PayloadSerializer(JSONSerializer):
    def __init__(self):
        super().__init__()
        self.additional_fields = {}
        self.extra_dict_data = {}
        self.obj_id_name = "id"

    def serialize(self, queryset, **options):
        self.additional_fields = options.pop("additional_fields", {})
        self.extra_dict_data = options.pop("extra_dict_data", {})
        self.obj_id_name = options.pop("obj_id_name", "id")
        return super().serialize(
            queryset,
            stream=options.pop("stream", None),
            fields=options.pop("fields", None),
            use_natural_foreign_keys=options.pop("use_natural_foreign_keys", False),
            use_natural_primary_keys=options.pop("use_natural_primary_keys", False),
            progress_output=options.pop("progress_output", None),
            object_count=options.pop("object_count", 0),
            **options,
        )

    def get_dump_object(self, obj):
        obj_id = graphene.Node.to_global_id(
            obj._meta.object_name, getattr(obj, self.obj_id_name)
        )
        data = OrderedDict(
            [("type", str(obj._meta.object_name)), (self.obj_id_name, obj_id)]
        )
        # Evaluate and add the "additional fields"
        python_serializer = PythonSerializer()
        for field_name, (qs, fields) in self.additional_fields.items():
            data_to_serialize = qs(obj)
            if not data_to_serialize:
                data[field_name] = None
            elif isinstance(data_to_serialize, Iterable):
                data[field_name] = python_serializer.serialize(
                    data_to_serialize, fields=fields
                )
            else:
                data[field_name] = python_serializer.serialize(
                    [data_to_serialize], fields=fields
                )[0]
        # Update the data with the  "extra dict data"
        called_data = {}
        for key, value in self.extra_dict_data.items():
            if callable(value):
                called_data[key] = value(obj)
        data.update(self.extra_dict_data)
        data.update(called_data)
        # Finally update the data with the super class' "self._current" content
        data.update(self._current)
        return data
