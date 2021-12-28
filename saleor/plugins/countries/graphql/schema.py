import graphene

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.connection import create_connection_slice
from ....graphql.core.federation import build_federated_schema
from ....graphql.core.fields import ConnectionField
from .. import models
from . import mutations, types


class Queries(graphene.ObjectType):
    cities = ConnectionField(
        types.CityCountableConnection,
        description="Query cities by country code.",
        code=graphene.Argument(
            CountryCodeEnum, description="Country code.", required=True
        ),
    )

    country_areas = ConnectionField(
        types.CountryAreaCountableConnection,
        description="Query country areas by country code.",
        code=graphene.Argument(
            CountryCodeEnum, description="Country code.", required=True
        ),
    )

    def resolve_cities(root, info, code, **data):
        qs = models.City.objects.filter(country=code)
        return create_connection_slice(qs, info, data, types.CityCountableConnection)

    def resolve_country_areas(root, info, code, **data):
        qs = models.CountryArea.objects.filter(country=code)
        return create_connection_slice(
            qs, info, data, types.CountryAreaCountableConnection
        )


class Mutations(graphene.ObjectType):
    city_create = mutations.CityCreate.Field()
    country_are_create = mutations.CountryAreaCreate.Field()


schema = build_federated_schema(
    query=Queries, mutation=Mutations, types=[types.City, types.CountryArea]
)
