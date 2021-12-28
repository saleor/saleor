import graphene

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.mutations import ModelMutation
from ....graphql.core.types.common import PluginError
from .. import models


class NameCountryInput(graphene.InputObjectType):
    name = graphene.String(description="City name", required=True)
    country = CountryCodeEnum(description="Country.")


class CityCreate(ModelMutation):
    class Arguments:
        input = NameCountryInput(
            description="Fields required to create a city.", required=True
        )

    class Meta:
        description = "Create a new city."
        model = models.City
        error_type_class = PluginError


class CountryAreaCreate(ModelMutation):
    class Arguments:
        input = NameCountryInput(
            description="Fields required to create a country area.", required=True
        )

    class Meta:
        description = "Create a new country area."
        model = models.CountryArea
        error_type_class = PluginError
