import graphene
from graphene import relay

from ....graphql.core.connection import CountableDjangoObjectType
from .. import models


class RegionNode(CountableDjangoObjectType):
    class Meta:
        model = models.Region
        filter_fields = [
            "id",
            "display_name",
            "geoname_code",
        ]
        interfaces = (graphene.relay.Node,)


class City(CountableDjangoObjectType):
    region = graphene.Field(RegionNode)

    class Meta:
        model = models.City
        filter_fields = [
            "id",
            "display_name",
            "latitude",
            "longitude",
            "subregion",
            "region",
            "country",
        ]
        interfaces = (graphene.relay.Node,)


class CityConnection(relay.Connection):
    class Meta:
        node = City


class CountryNode(CountableDjangoObjectType):
    class Meta:
        model = models.Country
        filter_fields = [
            "id",
            "continent",
            "phone",
        ]
        interfaces = (graphene.relay.Node,)


class CountryConnection(relay.Connection):
    class Meta:
        node = CountryNode
