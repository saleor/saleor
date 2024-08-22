from django.core.validators import MaxLengthValidator
from django.db import models

from ..core.utils.translations import Translation


class SeoModel(models.Model):
    seo_title = models.CharField(
        max_length=70, blank=True, null=True, validators=[MaxLengthValidator(70)]
    )
    seo_description = models.CharField(
        max_length=300, blank=True, null=True, validators=[MaxLengthValidator(300)]
    )

    class Meta:
        abstract = True


class SeoModelTranslation(Translation):
    seo_title = models.CharField(
        max_length=70, blank=True, null=True, validators=[MaxLengthValidator(70)]
    )
    seo_description = models.CharField(
        max_length=300, blank=True, null=True, validators=[MaxLengthValidator(300)]
    )

    class Meta:
        abstract = True

    def get_translated_keys(self):
        return {
            "seo_title": self.seo_title,
            "seo_description": self.seo_description,
        }


class SeoModelTranslationWithSlug(SeoModelTranslation):
    slug = models.SlugField(max_length=255, allow_unicode=True, null=True)

    class Meta:
        abstract = True

    def get_translated_keys(self):
        translated_keys = super().get_translated_keys()
        translated_keys["slug"] = self.slug

        return translated_keys
