import graphene

from ...tax import models
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.types import Channel
from ..core import ResolveInfo
from ..core.connection import CountableConnection
from ..core.descriptions import ADDED_IN_319, ADDED_IN_321
from ..core.doc_category import DOC_CATEGORY_TAXES
from ..core.types import BaseObjectType, CountryDisplay, ModelObjectType, NonNullList
from ..meta.types import ObjectWithMetadata
from .dataloaders import (
    TaxClassByIdLoader,
    TaxClassCountryRateByTaxClassIDLoader,
    TaxConfigurationPerCountryByTaxConfigurationIDLoader,
)
from .enums import TaxCalculationStrategy


class TaxConfiguration(ModelObjectType[models.TaxConfiguration]):
    channel = graphene.Field(
        Channel,
        description="A channel to which the tax configuration applies to.",
        required=True,
    )
    charge_taxes = graphene.Boolean(
        description="Determines whether taxes are charged in the given channel.",
        required=True,
    )
    tax_calculation_strategy = graphene.Field(
        TaxCalculationStrategy,
        required=False,
        description=(
            "The default strategy to use for tax calculation in the given channel. "
            "Taxes can be calculated either using user-defined flat rates or with "
            "a tax app. Empty value means that no method is selected and taxes are "
            "not calculated."
        ),
    )
    display_gross_prices = graphene.Boolean(
        description="Determines whether displayed prices should include taxes.",
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
    tax_app_id = graphene.String(
        description=(
            "The tax app `App.identifier` that will be used to calculate the taxes for the given channel. "
            "Empty value for `TAX_APP` set as `taxCalculationStrategy` means that Saleor will "
            "iterate over all installed tax apps. If multiple tax apps exist with provided "
            "tax app id use the `App` with newest `created` date. "
            "Will become mandatory in 4.0 for `TAX_APP` `taxCalculationStrategy`."
            + ADDED_IN_319
        ),
        required=False,
    )
    use_weighted_tax_for_shipping = graphene.Boolean(
        description=(
            "Determines whether to use weighted tax for shipping. When set to true, "
            "the tax rate for shipping will be calculated based on the weighted average "
            "of tax rates from the order or checkout lines." + ADDED_IN_321
        ),
    )

    class Meta:
        description = "Channel-specific tax configuration."
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.TaxConfiguration

    @staticmethod
    def resolve_channel(root: models.TaxConfiguration, info: ResolveInfo):
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    def resolve_countries(root: models.TaxConfiguration, info: ResolveInfo):
        return TaxConfigurationPerCountryByTaxConfigurationIDLoader(info.context).load(
            root.pk
        )

    @staticmethod
    def resolve_use_weighted_tax_for_shipping(
        root: models.TaxConfiguration, info: ResolveInfo
    ):
        return root.use_weighted_tax_for_shipping


class TaxConfigurationCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_TAXES
        node = TaxConfiguration


class TaxConfigurationPerCountry(ModelObjectType[models.TaxConfigurationPerCountry]):
    country = graphene.Field(
        CountryDisplay,
        required=True,
        description="Country in which this configuration applies.",
    )
    charge_taxes = graphene.Boolean(
        description="Determines whether taxes are charged in this country.",
        required=True,
    )
    tax_calculation_strategy = graphene.Field(
        TaxCalculationStrategy,
        required=False,
        description=(
            "A country-specific strategy to use for tax calculation. Taxes can be "
            "calculated either using user-defined flat rates or with a tax app. If "
            "not provided, use the value from the channel's tax configuration."
        ),
    )
    display_gross_prices = graphene.Boolean(
        description=(
            "Determines whether displayed prices should include taxes for this country."
        ),
        required=True,
    )
    tax_app_id = graphene.String(
        description=(
            "The tax app `App.identifier` that will be used to calculate the taxes for the given channel "
            "and country. If not provided, use the value from the channel's tax configuration."
            + ADDED_IN_319
        ),
        required=False,
    )
    use_weighted_tax_for_shipping = graphene.Boolean(
        description=(
            "Determines whether to use weighted tax for shipping. When set to true, "
            "the tax rate for shipping will be calculated based on the weighted average "
            "of tax rates from the order or checkout lines." + ADDED_IN_321
        ),
    )

    class Meta:
        description = "Country-specific exceptions of a channel's tax configuration."
        interface = [graphene.relay.Node]
        model = models.TaxConfigurationPerCountry

    @staticmethod
    def resolve_country(root: models.TaxConfigurationPerCountry, _info: ResolveInfo):
        return CountryDisplay(code=root.country.code, country=root.country.name)

    @staticmethod
    def resolve_use_weighted_tax_for_shipping(
        root: models.TaxConfiguration, info: ResolveInfo
    ):
        return root.use_weighted_tax_for_shipping


class TaxClass(ModelObjectType[models.TaxClass]):
    name = graphene.String(description="Name of the tax class.", required=True)
    countries = NonNullList(
        "saleor.graphql.tax.types.TaxClassCountryRate",
        required=True,
        description="Country-specific tax rates for this tax class.",
    )

    class Meta:
        description = (
            "Tax class is a named object used to define tax rates per country. Tax "
            "class can be assigned to product types, products and shipping methods to "
            "define their tax rates."
        )
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.TaxClass

    @staticmethod
    def resolve_countries(root: models.TaxConfiguration, info):
        return TaxClassCountryRateByTaxClassIDLoader(info.context).load(root.pk)


class TaxClassCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_TAXES
        node = TaxClass


class TaxClassCountryRate(ModelObjectType[models.TaxClassCountryRate]):
    country = graphene.Field(
        CountryDisplay,
        required=True,
        description="Country in which this tax rate applies.",
    )
    rate = graphene.Float(required=True, description="Tax rate value.")
    tax_class = graphene.Field(
        TaxClass, description="Related tax class.", required=False
    )

    class Meta:
        description = (
            "Tax rate for a country. When tax class is null, it represents the default "
            "tax rate for that country; otherwise it's a country tax rate specific to "
            "the given tax class."
        )
        model = models.TaxClassCountryRate

    @staticmethod
    def resolve_country(root: models.TaxConfigurationPerCountry, _info: ResolveInfo):
        return CountryDisplay(code=root.country.code, country=root.country.name)

    @staticmethod
    def resolve_tax_class(root, info: ResolveInfo):
        return (
            TaxClassByIdLoader(info.context).load(root.tax_class_id)
            if root.tax_class_id
            else None
        )


class TaxCountryConfiguration(BaseObjectType):
    country = graphene.Field(
        CountryDisplay,
        required=True,
        description="A country for which tax class rates are grouped.",
    )
    tax_class_country_rates = NonNullList(
        TaxClassCountryRate, description="List of tax class rates.", required=True
    )

    class Meta:
        description = "Tax class rates grouped by country."
        doc_category = DOC_CATEGORY_TAXES

    @staticmethod
    def resolve_country(root, _info: ResolveInfo, **kwargs):
        return CountryDisplay(code=root.country.code, country=root.country.name)
