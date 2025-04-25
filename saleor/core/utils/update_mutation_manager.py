from copy import deepcopy
from typing import Any


class InstanceTracker:
    """Instance with modifications tracker."""

    def __init__(self, instance, fields_to_track):
        self.instance = instance
        self.fields_to_track = fields_to_track
        self.initial_instance_values: dict[str, Any] = deepcopy(self.get_field_values())

    def get_field_values(self) -> dict[str, Any]:
        return {
            field: getattr(self.instance, field, None) for field in self.fields_to_track
        }

    def get_modified_fields(self) -> list[str]:
        modified_instance_values: dict[str, Any] = self.get_field_values()
        return [
            field
            for field in self.initial_instance_values.keys()
            if self.initial_instance_values.get(field)
            != modified_instance_values.get(field)
        ]
