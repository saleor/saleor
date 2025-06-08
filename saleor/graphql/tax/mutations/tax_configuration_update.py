from typing import Any

import graphene
from django.core.exceptions import ValidationError

from ....app.utils import get_active_tax_apps
from ....permission.enums import CheckoutPermissions
from ....plugins import PLUGIN_IDENTIFIER_PREFIX
from ....tax import error_codes, models
from ...account.enums import CountryCodeEnum
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_319, ADDED_IN_321
from ...core.doc_category import DOC_CATEGORY_TAXES
from ...core.mutations import DeprecatedModelMutation
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
    use_weighted_tax_for_shipping = graphene.Boolean(
        description=(
            "Determines whether to use weighted tax for shipping. When set to true, "
            "the tax rate for shipping will be calculated based on the weighted average "
            "of tax rates from the order or checkout lines. Default value is `False`."
            "Can be used only with `taxCalculationStrategy` set to `FLAT_RATES`."
            + ADDED_IN_321
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
    use_weighted_tax_for_shipping = graphene.Boolean(
        description=(
            "Determines whether to use weighted tax for shipping. When set to true, "
            "the tax rate for shipping will be calculated based on the weighted average "
            "of tax rates from the order or checkout lines. Default value is `False`."
            "Can be used only with `taxCalculationStrategy` set to `FLAT_RATES`."
            + ADDED_IN_321
        ),
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


class TaxConfigurationUpdate(DeprecatedModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of the tax configuration.", required=True)
        input = TaxConfigurationUpdateInput(
            description="Fields required to update the tax configuration.",
            required=True,
        )

    class Meta:
        description = "Update tax configuration for a channel."
        error_type_class = TaxConfigurationUpdateError
        model = models.TaxConfiguration
        object_type = TaxConfiguration
        permissions = (CheckoutPermissions.MANAGE_TAXES,)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cls.clean_tax_app_id(info, instance, data)
        cls.clean_use_weighted_tax_for_shipping(info, instance, data)
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
    def _clean_use_weighted_tax_for_shipping(
        cls,
        instance: models.TaxConfiguration | models.TaxConfigurationPerCountry,
        data: dict[str, Any],
    ):
        use_weighted_tax_for_shipping = data.get("use_weighted_tax_for_shipping")
        if use_weighted_tax_for_shipping is None:
            use_weighted_tax_for_shipping = instance.use_weighted_tax_for_shipping
        if use_weighted_tax_for_shipping:
            current_tax_strategy = (
                data.get("tax_calculation_strategy")
                or instance.tax_calculation_strategy
            )
            if current_tax_strategy != TaxCalculationStrategy.FLAT_RATES.value:
                message = "`useWeightedTaxForShipping` can be used only with `taxCalculationStrategy` set to `FLAT_RATES`."
                raise ValidationError(message=message)

    @classmethod
    def clean_use_weighted_tax_for_shipping(
        cls, info: ResolveInfo, instance: TaxConfiguration, data: dict[str, Any]
    ):
        try:
            cls._clean_use_weighted_tax_for_shipping(instance, data)
        except ValidationError as e:
            raise ValidationError(
                {
                    "use_weighted_tax_for_shipping": ValidationError(
                        message=e.message,
                        code=error_codes.TaxConfigurationUpdateErrorCode.INVALID.value,
                        params={"country_codes": []},
                    )
                }
            ) from e

        if update_countries_configuration := data.get(
            "update_countries_configuration", []
        ):
            error_country_codes = []
            country_exceptions = instance.country_exceptions.filter(
                country__in=[
                    country_data["country_code"]
                    for country_data in update_countries_configuration
                ]
            )
            input_country_exception_map = {
                country_data["country_code"]: country_data
                for country_data in update_countries_configuration
            }

            for country_exception in country_exceptions:
                try:
                    cls._clean_use_weighted_tax_for_shipping(
                        country_exception,
                        input_country_exception_map[country_exception.country],
                    )
                except ValidationError:
                    error_country_codes.append(country_exception.country.code)
            if error_country_codes:
                raise ValidationError(
                    {
                        "use_weighted_tax_for_shipping": ValidationError(
                            message="`useWeightedTaxForShipping` can be used only "
                            "with `taxCalculationStrategy` set to `FLAT_RATES` for "
                            "country codes: " + ", ".join(error_country_codes),
                            code=error_codes.TaxConfigurationUpdateErrorCode.INVALID.value,
                            params={"country_codes": error_country_codes},
                        )
                    }
                )

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
        country_codes=None,
    ):
        if country_codes is None:
            country_codes = []
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

            if data.get("use_weighted_tax_for_shipping") is not None:
                obj.use_weighted_tax_for_shipping = data[
                    "use_weighted_tax_for_shipping"
                ]

            updated_countries.append(obj.country.code)

        models.TaxConfigurationPerCountry.objects.bulk_update(
            to_update,
            fields=(
                "charge_taxes",
                "display_gross_prices",
                "tax_calculation_strategy",
                "tax_app_id",
                "use_weighted_tax_for_shipping",
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
                use_weighted_tax_for_shipping=item.get(
                    "use_weighted_tax_for_shipping", False
                ),
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
