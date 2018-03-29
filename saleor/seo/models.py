from django.core.validators import MaxLengthValidator
from django.db import models


class SeoModel(models.Model):
    seo_title = models.CharField(
        max_length=70, blank=True, null=True,
        validators=[MaxLengthValidator(70)])
    seo_description = models.CharField(
        max_length=300, blank=True, null=True,
        validators=[MaxLengthValidator(300)])

    class Meta:
        abstract = True
