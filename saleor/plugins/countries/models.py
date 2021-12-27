from django.db import models
from django_countries.fields import CountryField

from ...core.utils.translations import TranslationProxy


class City(models.Model):
    name = models.CharField(max_length=256)
    country = CountryField()
    translated = TranslationProxy()


class CountryArea(models.Model):
    name = models.CharField(max_length=256)
    country = CountryField()
    translated = TranslationProxy()
