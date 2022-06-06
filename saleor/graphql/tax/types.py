import graphene

from ...tax import models
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.types import Channel
from ..core.connection import CountableConnection
from ..core.descriptions import ADDED_IN_35, PREVIEW_FEATURE
from ..core.types import CountryDisplay, ModelObjectType, NonNullList
from ..meta.types import ObjectWithMetadata
from .dataloaders import (
    TaxClassByIdLoader,
    TaxClassCountryRateByTaxClassIDLoader,
    TaxConfigurationPerCountryByTaxConfigurationIDLoader,
)


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
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
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


class TaxClass(ModelObjectType):
    name = graphene.String(description="Name of the tax class.", required=True)
    is_default = graphene.Boolean(
        description=(
            "Determines whether a tax class is a default one. Default tax class is "
            "created by the system and cannot be removed."
        ),
        required=True,
    )
    countries = NonNullList(
        "saleor.graphql.tax.types.TaxClassCountryRate",
        required=True,
        description="Country-specific tax rates for this tax class.",
    )

    class Meta:
        description = (
            "Tax class is a named object used to define tax rates per country. Tax "
            "class can be assigned to product types, products and shipping methods to "
            "define their tax rates." + ADDED_IN_35 + PREVIEW_FEATURE
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.TaxClass

    @staticmethod
    def resolve_countries(root: models.TaxConfiguration, info):
        return TaxClassCountryRateByTaxClassIDLoader(info.context).load(root.pk)


class TaxClassCountableConnection(CountableConnection):
    class Meta:
        node = TaxClass


class TaxClassCountryRate(ModelObjectType):
    country = graphene.Field(
        CountryDisplay,
        required=True,
        description="Country in which this tax rate applies.",
    )
    rate = graphene.Float(required=True, description="Tax rate value.")
    tax_class = graphene.Field(
        TaxClass, description="Related tax class.", required=True
    )

    class Meta:
        description = (
            "Country-specific tax rate value for a tax class."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )
        model = models.TaxClassCountryRate

    @staticmethod
    def resolve_country(root: models.TaxConfigurationPerCountry, _info):
        return CountryDisplay(code=root.country.code, country=root.country.name)

    @staticmethod
    def resolve_tax_class(root, info):
        return TaxClassByIdLoader(info.context).load(root.tax_class_id)


class TaxCountryConfiguration(graphene.ObjectType):
    country = graphene.Field(
        CountryDisplay,
        required=True,
        description="A country for which tax class rates are grouped.",
    )
    tax_class_country_rates = NonNullList(
        TaxClassCountryRate, description="List of tax class rates.", required=True
    )

    class Meta:
        description = (
            "Tax class rates grouped by country." + ADDED_IN_35 + PREVIEW_FEATURE
        )

    @staticmethod
    def resolve_country(root, info, **kwargs):
        return CountryDisplay(code=root.country.code, country=root.country.name)
