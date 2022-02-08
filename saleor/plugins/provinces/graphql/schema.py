import graphene

from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.core.utils import from_global_id_or_error

from ....graphql.core.connection import create_connection_slice
from ....graphql.core.federation import build_federated_schema
from .. import models
from . import types


class Query(graphene.ObjectType):

    cities = FilterConnectionField(types.CityConnection)
    city = graphene.Field(
        types.City,
        id=graphene.Argument(graphene.ID, description="ID of the city", required=True),
        description="Look up a city by ID",
    )
    country = graphene.Field(
        types.CountryNode,
        code2=graphene.Argument(
            graphene.String, description="ID of the Country", required=True
        ),
        description="Look up a Country by ID",
    )
    countries = FilterConnectionField(types.CountryConnection)

    def resolve_cities(root, info, **kwargs):
        qs = models.City.objects.all()
        return create_connection_slice(qs, info, kwargs, types.CityConnection)

    def resolve_city(self, info, id, **data):
        _, id = from_global_id_or_error(id, types.City)
        return models.City.objects.get(id=id)

    def resolve_country(self, info, code2, **data):
        # _, id = from_global_id_or_error(id, types.CountryNode)
        return models.Country.objects.get(code2=code2)

    def resolve_countries(root, info, **kwargs):
        qs = models.Country.objects.all()
        return create_connection_slice(qs, info, kwargs, types.CountryConnection)


schema = build_federated_schema(query=Query, types=[types.City])
