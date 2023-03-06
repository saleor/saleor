import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from django_countries.fields import Country
from graphql import GraphQLError

from ....core.permissions import CheckoutPermissions
from ....tax import error_codes, models
from ...account.enums import CountryCodeEnum
from ...core.descriptions import ADDED_IN_39, PREVIEW_FEATURE
from ...core.mutations import BaseMutation
from ...core.types import Error, NonNullList
from ...core.utils import from_global_id_or_error
from ..types import TaxCountryConfiguration

TaxCountryConfigurationUpdateErrorCode = graphene.Enum.from_enum(
    error_codes.TaxCountryConfigurationUpdateErrorCode
)


class TaxCountryConfigurationUpdateError(Error):
    code = TaxCountryConfigurationUpdateErrorCode(
        description="The error code.", required=True
    )
    tax_class_ids = NonNullList(
        graphene.String,
        description="List of tax class IDs for which the update failed.",
        required=True,
    )


class TaxClassRateInput(graphene.InputObjectType):
    tax_class_id = graphene.ID(
        description="ID of a tax class for which to update the tax rate", required=False
    )
    rate = graphene.Float(description="Tax rate value.", required=False)


class TaxCountryConfigurationUpdate(BaseMutation):
    tax_country_configuration = graphene.Field(
        TaxCountryConfiguration,
        description="Updated tax class rates grouped by a country.",
    )

    class Arguments:
        country_code = CountryCodeEnum(
            description="Country in which to update the tax class rates.", required=True
        )
        update_tax_class_rates = NonNullList(
            TaxClassRateInput,
            description=(
                "List of tax rates per tax class to update. When "
                "`{taxClass: id, rate: null`} is passed, it deletes the rate object "
                "for given taxClass ID. When `{rate: Int}` is passed without a tax "
                "class, it updates the default tax class for this country."
            ),
            required=True,
        )

    class Meta:
        description = (
            "Update tax class rates for a specific country."
            + ADDED_IN_39
            + PREVIEW_FEATURE
        )
        error_type_class = TaxCountryConfigurationUpdateError
        permissions = (CheckoutPermissions.MANAGE_TAXES,)

    def _clean_default_rates(tax_rate_items):
        # Check if only one default rate is provided (only one item without the tax
        # class).
        default_rate_items = [
            item for item in tax_rate_items if item.get("tax_class_id") is None
        ]
        if len(default_rate_items) > 1:
            code = (
                error_codes.TaxCountryConfigurationUpdateErrorCode.ONLY_ONE_DEFAULT_COUNTRY_RATE_ALLOWED  # noqa: E501
            )
            params = {"tax_class_ids": []}
            raise ValidationError(
                {
                    "update_tax_class_rates": ValidationError(
                        code=code,
                        message=(
                            "Only one default country rate can be created for "
                            "a country (a rate without a tax class)."
                        ),
                        params=params,
                    )
                }
            )

    def _clean_tax_class_ids(tax_rate_items):
        cleaned_data = {}
        failed_ids = []
        for item in tax_rate_items:
            global_id = item.get("tax_class_id")
            pk = None
            if global_id:
                try:
                    _, pk = from_global_id_or_error(
                        global_id, "TaxClass", raise_error=True
                    )
                except GraphQLError:
                    failed_ids.append(global_id)
                    continue
                pk = int(pk)

            cleaned_data[pk] = item

        if failed_ids:
            params = {"tax_class_ids": failed_ids}
            code = error_codes.TaxCountryConfigurationUpdateErrorCode.NOT_FOUND
            message = "Failed to resolve some of the provided tax class IDs."
            raise ValidationError(
                {
                    "update_tax_class_rates": ValidationError(
                        code=code, message=message, params=params
                    )
                }
            )

        return cleaned_data

    @classmethod
    def _clean_rate_values(cls, tax_rate_items):
        invalid_rates = []
        for item in tax_rate_items:
            rate = item.get("rate")
            if rate is not None and rate < 0:
                invalid_rates.append(item)

        if invalid_rates:
            code = (
                error_codes.TaxCountryConfigurationUpdateErrorCode.CANNOT_CREATE_NEGATIVE_RATE  # noqa: E501
            )
            message = "Cannot create rates with negative values."
            params = {
                "tax_class_ids": [
                    item["tax_class_id"]
                    for item in invalid_rates
                    if item.get("tax_class_id")
                ]
            }
            raise ValidationError(
                {
                    "update_tax_class_rates": ValidationError(
                        code=code, message=message, params=params
                    )
                }
            )

    @classmethod
    def clean_input(cls, **data):
        update_tax_class_rates = data.get("update_tax_class_rates", [])
        cls._clean_rate_values(update_tax_class_rates)
        cls._clean_default_rates(update_tax_class_rates)
        return cls._clean_tax_class_ids(update_tax_class_rates)

    @classmethod
    def update_default_rate(cls, country_code, cleaned_data):
        # Handle the default country rate first (the one without a tax class).
        default_rate = cleaned_data.get(None)
        if default_rate:
            rate = default_rate.get("rate")
            if rate is not None:
                models.TaxClassCountryRate.objects.update_or_create(
                    country=country_code,
                    tax_class=None,
                    defaults={"rate": default_rate["rate"]},
                )
            else:
                default_rate_obj = models.TaxClassCountryRate.objects.filter(
                    country=country_code,
                    tax_class=None,
                ).first()
                if default_rate_obj:
                    default_rate_obj.delete()

    @classmethod
    def update_and_create_country_rates(cls, country_code, cleaned_data):
        # Prepare IDs to create and update.
        input_ids = [key for key in cleaned_data.keys() if key is not None]
        update_qs = models.TaxClassCountryRate.objects.filter(
            country=country_code, tax_class_id__in=input_ids
        )
        update_ids = [item.tax_class_id for item in update_qs]
        create_ids = set(input_ids) - set(update_ids)
        delete_ids = []

        # Update existing instances.
        for obj in update_qs:
            rate = cleaned_data[obj.tax_class_id].get("rate")
            if rate is None:
                delete_ids.append(obj.tax_class_id)
            else:
                obj.rate = rate
        models.TaxClassCountryRate.objects.bulk_update(update_qs, fields=("rate",))

        # Create new instances.
        to_create = []
        for tax_class_id in create_ids:
            input_item = cleaned_data[tax_class_id]
            rate = input_item.get("rate")
            if rate is not None:
                obj = models.TaxClassCountryRate(
                    country=country_code, tax_class_id=tax_class_id, rate=rate
                )
                to_create.append(obj)
        models.TaxClassCountryRate.objects.bulk_create(to_create)

        # Delete instances where null rates were provided.
        models.TaxClassCountryRate.objects.filter(
            country=country_code,
            tax_class_id__in=delete_ids,
        ).delete()

    @classmethod
    def perform_mutation(cls, _root, _info, **data):
        country_code = data["country_code"]
        cleaned_data = cls.clean_input(**data)
        cls.update_default_rate(country_code, cleaned_data)
        cls.update_and_create_country_rates(country_code, cleaned_data)

        tax_classes_lookup = Q(tax_class_id__in=cleaned_data.keys())
        if None in cleaned_data:
            tax_classes_lookup |= Q(tax_class=None)
        all_rates = models.TaxClassCountryRate.objects.filter(
            tax_classes_lookup, country=country_code
        )
        country_config = TaxCountryConfiguration(
            country=Country(country_code), tax_class_country_rates=all_rates
        )
        return TaxCountryConfigurationUpdate(tax_country_configuration=country_config)
