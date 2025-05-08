from typing import TypeVar

from django.db.models import Model
from model_utils import FieldTracker
from model_utils.tracker import FieldInstanceTracker

T = TypeVar("T", bound=Model)


class InstanceTrackerError(Exception):
    """Base class for tracker errors."""


class BaseFieldInstanceTracker(FieldInstanceTracker):

    def changed_fields(self, fields_to_track: list[str]) -> list[str]:
        """Return modified field names filtered by list of field names to track."""
        self._validate_fields_to_track(fields_to_track)
        modified_fields = super().changed()
        return [k for k, v in modified_fields.items() if k in fields_to_track]

    def _validate_fields_to_track(self, fields_to_track: list[str]):
        """Validate fields to track.

        Make sure fields_to_track contains only fields from database table.
        FieldTracker expect db column names for ForeignKey fields and not model names.
        """
        model_fields = {field.column for field in self.instance._meta.fields}
        absent_fields = [
            field for field in fields_to_track if field not in model_fields
        ]
        if absent_fields:
            absent_fields_str = ", ".join(absent_fields)
            raise InstanceTrackerError(
                f"Fields: [{absent_fields_str}] are not present in database table. "
                f"Make sure to use db column names in fields to track.."
            )


class InstanceTracker(FieldTracker):
    tracker_class = BaseFieldInstanceTracker
