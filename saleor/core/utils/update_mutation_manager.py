from typing import Any, TypeVar

from django.db.models import Model

N = TypeVar("N", bound=Model)


class InstanceTracker:
    """Instance with modifications tracker."""

    def __init__(self, instance: N):
        self.instance = instance
        self.instance_editable_fields = [
            field.name
            for field in self.instance._meta.model._meta.fields
            if field.editable
        ]
        self.initial_instance_values: dict[str, Any] = self.get_field_values()

    def get_field_values(self) -> dict[str, Any]:
        return {
            field: getattr(self.instance, field, None)
            for field in self.instance_editable_fields
        }

    def get_modified_fields(self) -> list[str]:
        modified_instance_values: dict[str, Any] = self.get_field_values()
        return [
            field
            for field in self.initial_instance_values.keys()
            if self.initial_instance_values.get(field)
            != modified_instance_values.get(field)
        ]
