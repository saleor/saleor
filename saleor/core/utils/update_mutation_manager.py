from copy import deepcopy
from typing import Any, TypeVar

from django.db.models import Model

T = TypeVar("T", bound=Model)


class InstanceTracker:
    """Instance with modifications tracker.

    It is used to determine modified fields of the instance.
    """

    def __init__(
        self,
        instance: T | None,
        fields_to_track: list[str],
        foreign_fields_to_track: dict[str, list[str]] | None = None,
    ):
        self.instance = instance
        self.fields_to_track = fields_to_track
        self.initial_instance_values: dict[str, Any] = (
            deepcopy(self.get_field_values()) if instance else {}
        )
        self.foreign_instance_relation: dict[str, InstanceTracker] = {}
        self.create = instance is None

        if foreign_fields_to_track:
            for lookup, fields in foreign_fields_to_track.items():
                foreign_instance = getattr(instance, lookup, None)
                self.foreign_instance_relation[lookup] = InstanceTracker(
                    foreign_instance,
                    fields,
                    None,
                )

    def get_field_values(self) -> dict[str, Any]:
        """Create a dict of tracked fields with related instance values."""
        if not self.instance:
            return {}

        return {field: getattr(self.instance, field) for field in self.fields_to_track}

    def get_modified_fields(self) -> list[str]:
        """Compare updated instance values with initial ones.

        Raise exception when instance is None.
        """
        if not self.initial_instance_values:
            if self.instance:
                return self.fields_to_track
            return []

        modified_instance_values: dict[str, Any] = self.get_field_values()
        return [
            field
            for field in self.initial_instance_values
            if self.initial_instance_values.get(field)
            != modified_instance_values.get(field)
        ]

    def get_foreign_modified_fields(self) -> dict[str, list[str]]:
        modified_fields = {}
        for lookup, tracker in self.foreign_instance_relation.items():
            tracker.instance = getattr(self.instance, lookup, None)
            foreign_modified = tracker.get_modified_fields()
            if foreign_modified:
                modified_fields[lookup] = foreign_modified
        return modified_fields
