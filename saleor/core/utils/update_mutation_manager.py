from typing import Any, TypeVar

from django.db.models import Model


def get_editable_values_from_instance(instance):
    field_names = [
        field.name for field in instance._meta.model._meta.fields if field.editable
    ]
    instance_values = {
        field_name: getattr(instance, field_name) for field_name in field_names
    }
    return instance_values


def get_edited_fields(old_values: dict, new_values: dict):
    return [
        field
        for field in old_values.keys()
        if old_values.get(field) != new_values.get(field)
    ]


N = TypeVar("N", bound=Model)


class InstanceTracker:
    """Instance with modifications tracker."""

    def __init__(
        self,
        instance: N,
        instance_editable_fields: list[str],
    ):
        self.instance = instance
        self.instance_editable_fields = instance_editable_fields
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

    def save_instance(self) -> bool:
        if modified_fields := self.get_modified_fields():
            modified_fields.append("updated_at")
            self.instance.save(update_fields=modified_fields)
            return True
        return False

    def metadata_modified(self) -> bool:
        if modified_fields := self.get_modified_fields():
            return (
                "metadata" in modified_fields or "private_metadata" in modified_fields
            )
        return False
