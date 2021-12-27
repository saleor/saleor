from ....graphql.core.connection import CountableConnection, CountableDjangoObjectType
from ....graphql.translations.fields import TranslationField
from .. import models
from .translations import CityTranslation, CountryAreaTranslation


class City(CountableDjangoObjectType):
    translation = TranslationField(
        CityTranslation,
        type_name="city",
    )

    class Meta:
        model = models.City


class CityCountableConnection(CountableConnection):
    class Meta:
        node = City


class CountryArea(CountableDjangoObjectType):
    translation = TranslationField(
        CountryAreaTranslation,
        type_name="country area",
    )

    class Meta:
        model = models.CountryArea


class CountryAreaCountableConnection(CountableConnection):
    class Meta:
        node = CountryArea
