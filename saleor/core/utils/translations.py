from typing import Any, Union

from django.conf import settings
from django.db import models


class TranslationWrapper:
    def __init__(self, instance, locale):
        self.instance = instance
        self.translation = next(
            (t for t in instance.translations.all() if t.language_code == locale), None
        )

    def __getattr__(self, item):
        if all(
            [
                item not in ["id", "pk"],
                self.translation is not None,
                hasattr(self.translation, item),
            ]
        ):
            return getattr(self.translation, item)
        return getattr(self.instance, item)

    def __str__(self):
        instance = self.translation or self.instance
        return str(instance)


class Translation(models.Model):
    language_code = models.CharField(max_length=35)

    class Meta:
        abstract = True

    def get_translated_object_id(self) -> tuple[str, Union[int, str]]:
        raise NotImplementedError(
            "Models extending Translation should implement get_translated_object_id"
        )

    def get_translated_keys(self) -> dict[str, Any]:
        raise NotImplementedError(
            "Models extending Translation should implement get_translated_keys"
        )

    def get_translation_context(self) -> dict[str, Any]:
        return {}


def get_translation(instance, language_code=None) -> TranslationWrapper:
    if not language_code:
        language_code = settings.LANGUAGE_CODE
    return TranslationWrapper(instance, language_code)
