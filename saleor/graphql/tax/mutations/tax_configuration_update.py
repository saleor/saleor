import graphene
from django.core.exceptions import ValidationError

from ....app.utils import get_active_tax_apps
from ....permission.enums import CheckoutPermissions
from ....plugins import PLUGIN_IDENTIFIER_PREFIX
from ....tax import error_codes, models
from ...account.enums import CountryCodeEnum
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_39, ADDED_IN_319
from ...core.doc_category import DOC_CATEGORY_TAXES
from ...core.mutations import ModelMutation
from ...core.types import BaseInputObjectType, Error, NonNullList
from ...core.utils import get_duplicates_items
from ...plugins.dataloaders import get_plugin_manager_promise
from ..enums import TaxCalculationStrategy
from ..types import TaxConfiguration

TaxConfigurationUpdateErrorCode = graphene.Enum.from_enum(
    error_codes.TaxConfigurationUpdateErrorCode
)
TaxConfigurationUpdateErrorCode.doc_category = DOC_CATEGORY_TAXES


class TaxConfigurationPerCountryInput(BaseInputObjectType):
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
            "Determines whether displayed prices should include taxes for this country."
        ),
        required=True,
    )
    tax_app_id = graphene.String(
        description=(
            "The tax app `App.identifier` that will be used to calculate the taxes for the "
            "given channel and country. If not provided, use the value from the channel's "
            "tax configuration." + ADDED_IN_319
        ),
    )

    class Meta:
        doc_category = DOC_CATEGORY_TAXES


class TaxConfigurationUpdateInput(BaseInputObjectType):
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
        description="Determines whether displayed prices should include taxes."
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
    tax_app_id = graphene.String(
        description=(
            "The tax app `App.identifier` that will be used to calculate the taxes for the given channel. "
            "Empty value for `TAX_APP` set as `taxCalculationStrategy` means that Saleor will "
            "iterate over all installed tax apps. If multiple tax apps exist with provided "
            "tax app id use the `App` with newest `created` date. It's possible to set plugin "
            "by using prefix `plugin:` with `PLUGIN_ID` "
            "e.g. with Avalara `plugin:mirumee.taxes.avalara`."
            "Will become mandatory in 4.0 for `TAX_APP` `taxCalculationStrategy`."
            + ADDED_IN_319
        ),
    )

    class Meta:
        doc_category = DOC_CATEGORY_TAXES


class TaxConfigurationUpdateError(Error):
    code = TaxConfigurationUpdateErrorCode(description="The error code.", required=True)
    country_codes = NonNullList(
        graphene.String,
        description="List of country codes for which the configuration is invalid.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_TAXES


class TaxConfigurationUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of the tax configuration.", required=True)
        input = TaxConfigurationUpdateInput(
            description="Fields required to update the tax configuration.",
            required=True,
        )

    class Meta:
        description = "Update tax configuration for a channel." + ADDED_IN_39
        error_type_class = TaxConfigurationUpdateError
        model = models.TaxConfiguration
        object_type = TaxConfiguration
        permissions = (CheckoutPermissions.MANAGE_TAXES,)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cls.clean_tax_app_id(info, instance, data)
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
            code = (
                error_codes.TaxConfigurationUpdateErrorCode.DUPLICATED_INPUT_ITEM.value
            )
            raise ValidationError(message=message, code=code, params=params)

        return super().clean_input(info, instance, data, **kwargs)

    @classmethod
    def clean_tax_app_id(cls, info: ResolveInfo, instance, data):
        identifiers = []
        if (app_identifier := data.get("tax_app_id")) is not None:
            identifiers.append(app_identifier)

        update_countries_configuration = data.get("update_countries_configuration", [])
        for country in update_countries_configuration:
            if (country_app_identifier := country.get("tax_app_id")) is not None:
                identifiers.append(country_app_identifier)

        active_tax_apps = list(get_active_tax_apps(identifiers))
        active_tax_app_identifiers = [app.identifier for app in active_tax_apps]

        # include plugin in list of possible tax apps
        manager = get_plugin_manager_promise(info.context).get()
        plugin_ids = [
            identifier.replace(PLUGIN_IDENTIFIER_PREFIX, "")
            for identifier in identifiers
            if identifier.startswith(PLUGIN_IDENTIFIER_PREFIX)
        ]
        valid_plugins = manager.get_plugins(
            instance.channel.slug, active_only=True, plugin_ids=plugin_ids
        )
        valid_plugin_identifiers = [
            PLUGIN_IDENTIFIER_PREFIX + plugin.PLUGIN_ID for plugin in valid_plugins
        ]
        active_tax_app_identifiers.extend(valid_plugin_identifiers)

        # validate input
        if app_identifier is not None:
            cls.__verify_tax_app_id(info, app_identifier, active_tax_app_identifiers)

        update_countries_configuration = data.get("update_countries_configuration", [])
        for country in update_countries_configuration:
            if (country_app_identifier := country.get("tax_app_id")) is not None:
                cls.__verify_tax_app_id(
                    info,
                    country_app_identifier,
                    active_tax_app_identifiers,
                    [country["country_code"]],
                )

    @classmethod
    def __verify_tax_app_id(
        cls,
        info: ResolveInfo,
        app_identifier,
        active_tax_app_identifiers,
        country_codes=[],
    ):
        if app_identifier not in active_tax_app_identifiers:
            message = "Did not found Tax App with provided taxAppId."
            code = error_codes.TaxConfigurationUpdateErrorCode.NOT_FOUND.value
            params = {"country_codes": country_codes}
            raise ValidationError(message=message, code=code, params=params)

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
            obj.tax_app_id = data.get("tax_app_id")
            updated_countries.append(obj.country.code)
        models.TaxConfigurationPerCountry.objects.bulk_update(
            to_update,
            fields=(
                "charge_taxes",
                "display_gross_prices",
                "tax_calculation_strategy",
                "tax_app_id",
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
                tax_app_id=item.get("tax_app_id"),
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
