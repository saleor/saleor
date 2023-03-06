import json
from typing import Callable

from django.db.models import JSONField


class SanitizedJSONField(JSONField):
    description = "A JSON field that runs a given sanitization method "
    "before saving into the database."

    def __init__(self, *args, sanitizer: Callable[[dict], dict], **kwargs):
        super(SanitizedJSONField, self).__init__(*args, **kwargs)
        self._sanitizer_method = sanitizer

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["sanitizer"] = self._sanitizer_method
        return name, path, args, kwargs

    def get_db_prep_save(self, value: dict, connection):
        """Sanitize the value for saving using the passed sanitizer."""
        return json.dumps(self._sanitizer_method(value))
