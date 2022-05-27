import graphene

from ...tax import models
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.types import Channel
from ..core.connection import CountableConnection
from ..core.descriptions import ADDED_IN_35, PREVIEW_FEATURE
from ..core.types import CountryDisplay, ModelObjectType, NonNullList
from .dataloaders import TaxConfigurationPerCountryByTaxConfigurationIDLoader


class TaxConfiguration(ModelObjectType):
    channel = graphene.Field(
        Channel,
        description="A channel to which the tax configuration applies to.",
        required=True,
    )
    charge_taxes = graphene.Boolean(
        description="Determines whether taxes are charged in the given channel.",
        required=True,
    )
    display_gross_prices = graphene.Boolean(
        description=(
            "Determines whether prices displayed in a storefront should include taxes."
        ),
        required=True,
    )
    prices_entered_with_tax = graphene.Boolean(
        description="Determines whether prices are entered with the tax included.",
        required=True,
    )
    countries = NonNullList(
        "saleor.graphql.tax.types.TaxConfigurationPerCountry",
        required=True,
        description="List of country-specific exceptions in tax configuration.",
    )

    class Meta:
        description = (
            "Channel-specific tax configuration." + ADDED_IN_35 + PREVIEW_FEATURE
        )
        interfaces = [graphene.relay.Node]
        model = models.TaxConfiguration

    @staticmethod
    def resolve_channel(root: models.TaxConfiguration, info):
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    def resolve_countries(root: models.TaxConfiguration, info):
        return TaxConfigurationPerCountryByTaxConfigurationIDLoader(info.context).load(
            root.pk
        )


class TaxConfigurationCountableConnection(CountableConnection):
    class Meta:
        node = TaxConfiguration


class TaxConfigurationPerCountry(ModelObjectType):
    country = graphene.Field(
        CountryDisplay,
        required=True,
        description="Country in which this configuration applies.",
    )
    charge_taxes = graphene.Boolean(
        description="Determines whether taxes are charged in this country.",
        required=True,
    )
    display_gross_prices = graphene.Boolean(
        description=(
            "Determines whether prices displayed in a storefront should include taxes "
            "for this country."
        ),
        required=True,
    )

    class Meta:
        description = (
            "Country-specific exceptions of a channel's tax configuration."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )
        interface = [graphene.relay.Node]
        model = models.TaxConfigurationPerCountry

    @staticmethod
    def resolve_country(root: models.TaxConfigurationPerCountry, _info):
        return CountryDisplay(code=root.country.code, country=root.country.name)
