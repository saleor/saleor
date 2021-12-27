import graphene

from ....graphql.translations.types import BaseTranslationType
from .. import models


class CityTranslation(BaseTranslationType):
    class Meta:
        model = models.City
        interfaces = [graphene.relay.Node]
        only_fields = ["name"]


class CountryAreaTranslation(BaseTranslationType):
    class Meta:
        model = models.CountryArea
        interfaces = [graphene.relay.Node]
        only_fields = ["name"]
