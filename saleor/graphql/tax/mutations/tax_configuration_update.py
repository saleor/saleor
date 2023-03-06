import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import CheckoutPermissions
from ....tax import error_codes, models
from ...account.enums import CountryCodeEnum
from ...core.descriptions import ADDED_IN_39, PREVIEW_FEATURE
from ...core.mutations import ModelMutation
from ...core.types import Error, NonNullList
from ...core.utils import get_duplicates_items
from ..enums import TaxCalculationStrategy
from ..types import TaxConfiguration

TaxConfigurationUpdateErrorCode = graphene.Enum.from_enum(
    error_codes.TaxConfigurationUpdateErrorCode
)


class TaxConfigurationPerCountryInput(graphene.InputObjectType):
    country_code = CountryCodeEnum(
        description="Country in which this configuration applies.", required=True
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
            "Determines whether prices displayed in a storefront should include taxes "
            "for this country."
        ),
        required=True,
    )


class TaxConfigurationUpdateInput(graphene.InputObjectType):
    charge_taxes = graphene.Boolean(
        description="Determines whether taxes are charged in the given channel."
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
        description=(
            "Determines whether prices displayed in a storefront should include taxes."
        )
    )
    prices_entered_with_tax = graphene.Boolean(
        description="Determines whether prices are entered with the tax included."
    )
    update_countries_configuration = NonNullList(
        TaxConfigurationPerCountryInput,
        description=(
            "List of tax country configurations to create or update (identified by a "
            "country code)."
        ),
    )
    remove_countries_configuration = NonNullList(
        CountryCodeEnum,
        description="List of country codes for which to remove the tax configuration.",
    )


class TaxConfigurationUpdateError(Error):
    code = TaxConfigurationUpdateErrorCode(description="The error code.", required=True)
    country_codes = NonNullList(
        graphene.String,
        description="List of country codes for which the configuration is invalid.",
        required=True,
    )


class TaxConfigurationUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of the tax configuration.", required=True)
        input = TaxConfigurationUpdateInput(
            description="Fields required to update the tax configuration.",
            required=True,
        )

    class Meta:
        description = (
            "Update tax configuration for a channel." + ADDED_IN_39 + PREVIEW_FEATURE
        )
        error_type_class = TaxConfigurationUpdateError
        model = models.TaxConfiguration
        object_type = TaxConfiguration
        permissions = (CheckoutPermissions.MANAGE_TAXES,)

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        update_countries_configuration = data.get("update_countries_configuration", [])
        update_country_codes = [
            item["country_code"] for item in update_countries_configuration
        ]
        remove_country_codes = data.get("remove_countries_configuration", [])

        if duplicated_country_codes := list(
            get_duplicates_items(update_country_codes, remove_country_codes)
        ):
            message = (
                "The same country code cannot be in both lists for updating and "
                "removing items: "
            ) + ", ".join(duplicated_country_codes)
            params = {"country_codes": duplicated_country_codes}
            code = error_codes.TaxConfigurationUpdateErrorCode.DUPLICATED_INPUT_ITEM
            raise ValidationError(message=message, code=code, params=params)

        return super().clean_input(info, instance, data, input_cls)

    @classmethod
    def update_countries_configuration(cls, instance, countries_configuration):
        input_data_by_country = {
            item["country_code"]: item for item in countries_configuration
        }

        # update existing instances
        to_update = instance.country_exceptions.filter(
            country__in=input_data_by_country.keys()
        )
        updated_countries = []
        for obj in to_update:
            data = input_data_by_country[obj.country]
            obj.charge_taxes = data["charge_taxes"]
            obj.display_gross_prices = data["display_gross_prices"]
            obj.tax_calculation_strategy = data.get("tax_calculation_strategy")
            updated_countries.append(obj.country.code)
        models.TaxConfigurationPerCountry.objects.bulk_update(
            to_update,
            fields=(
                "charge_taxes",
                "display_gross_prices",
                "tax_calculation_strategy",
            ),
        )

        # create new instances
        to_create = [
            models.TaxConfigurationPerCountry(
                tax_configuration=instance,
                country=item["country_code"],
                charge_taxes=item["charge_taxes"],
                tax_calculation_strategy=item.get("tax_calculation_strategy"),
                display_gross_prices=item["display_gross_prices"],
            )
            for item in countries_configuration
            if item["country_code"] not in updated_countries
        ]
        models.TaxConfigurationPerCountry.objects.bulk_create(to_create)

    @classmethod
    def remove_countries_configuration(cls, country_codes):
        models.TaxConfigurationPerCountry.objects.filter(
            country__in=country_codes
        ).delete()

    @classmethod
    def save(cls, _info, instance, cleaned_input):
        instance.save()
        update_countries_configuration = cleaned_input.get(
            "update_countries_configuration", []
        )
        remove_countries_configuration = cleaned_input.get(
            "remove_countries_configuration", []
        )
        cls.update_countries_configuration(instance, update_countries_configuration)
        cls.remove_countries_configuration(remove_countries_configuration)
