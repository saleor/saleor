import graphene

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.connection import create_connection_slice
from ....graphql.core.federation import build_federated_schema
from ....graphql.core.fields import ConnectionField
from .. import models
from . import types


class Query(graphene.ObjectType):
    provinces = ConnectionField(
        types.ProvinceCountableConnection,
        description="Query cities by country code.",
        country_code=graphene.Argument(
            CountryCodeEnum, description="Country code.", required=True
        ),
    )

    def resolve_provinces(root, info, country_code, **data):
        qs = models.Province.objects.filter(country=country_code)
        return create_connection_slice(
            qs, info, data, types.ProvinceCountableConnection
        )


schema = build_federated_schema(query=Query, types=[types.Province])
