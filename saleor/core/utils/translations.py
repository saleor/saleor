from typing import Any, Dict, Tuple, Union

from django.db import models
from django.utils.translation import get_language


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


class TranslationProxy:
    def __get__(self, instance, owner):
        locale = get_language()
        return TranslationWrapper(instance, locale)


class Translation(models.Model):
    language_code = models.CharField(max_length=35)

    class Meta:
        abstract = True

    def get_translated_object_id(self) -> Tuple[str, Union[int, str]]:
        raise NotImplementedError(
            "Models extending Translation should implement get_translated_object_id"
        )

    def get_translated_keys(self) -> Dict[str, Any]:
        raise NotImplementedError(
            "Models extending Translation should implement get_translated_keys"
        )

    def get_translation_context(self) -> Dict[str, Any]:
        return {}
