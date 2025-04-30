from copy import deepcopy
from typing import Any, TypeVar

from django.db.models import Model

T = TypeVar("T", bound=Model)


class InstanceTracker:
    """Instance with modifications tracker.

    It is used to determine modified fields of the instance.
    """

    def __init__(self, instance: T | None, fields_to_track: list[str]):
        self.instance = instance
        self.fields_to_track = fields_to_track
        self.initial_instance_values: dict[str, Any] = deepcopy(self.get_field_values())

    def get_field_values(self) -> dict[str, Any]:
        """Create a dict of tracked fields with related instance values."""
        return {
            field: getattr(self.instance, field, None) for field in self.fields_to_track
        }

    def get_modified_fields(self) -> list[str]:
        """Compare updated instance values with initial ones.

        Raise exception when instance is None.
        """
        if self.instance is None:
            raise Exception("Instance cannot be None")

        modified_instance_values: dict[str, Any] = self.get_field_values()
        return [
            field
            for field in self.initial_instance_values.keys()
            if self.initial_instance_values.get(field)
            != modified_instance_values.get(field)
        ]
