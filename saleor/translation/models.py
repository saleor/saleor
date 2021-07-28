from typing import Any, Dict

from django.db import models


class Translation(models.Model):
    language_code = models.CharField(max_length=10)

    class Meta:
        abstract = True

    def get_translated_object(self) -> Any:
        raise NotImplementedError(
            "Models extending Translation should implement get_translated_object"
        )

    def get_translated_keys(self) -> Dict[str, Any]:
        raise NotImplementedError(
            "Models extending Translation should implement get_translated_keys"
        )
