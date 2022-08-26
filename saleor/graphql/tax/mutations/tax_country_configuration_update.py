import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from django_countries.fields import Country
from graphql import GraphQLError

from ....core.permissions import TaxPermissions
from ....tax import error_codes, models
from ...account.enums import CountryCodeEnum
from ...core.descriptions import ADDED_IN_35, PREVIEW_FEATURE
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
    rate = graphene.Float(description="Tax rate value.", required=True)


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
            description="List of tax rates per tax class to update.",
            required=True,
        )

    class Meta:
        description = (
            "Update tax class rates for a specific country."
            + ADDED_IN_35
            + PREVIEW_FEATURE
        )
        error_type_class = TaxCountryConfigurationUpdateError
        permissions = (TaxPermissions.MANAGE_TAXES,)

    @classmethod
    def clean_input(cls, **data):
        update_tax_class_rates = data.get("update_tax_class_rates", [])

        cleaned_data = {}
        failed_ids = []

        for item in update_tax_class_rates:
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
    def update_and_create_country_rates(cls, country_code, cleaned_data):
        # updating existing instances
        to_update = models.TaxClassCountryRate.objects.filter(
            country=country_code, tax_class_id__in=cleaned_data.keys()
        )
        update_tax_classes = []
        for obj in to_update:
            obj.rate = cleaned_data[obj.tax_class_id]["rate"]
            update_tax_classes.append(obj.tax_class_id)
        models.TaxClassCountryRate.objects.bulk_update(to_update, fields=("rate",))

        # update the default country rate (without tax class)
        default_rate = cleaned_data.get(None)
        if default_rate:
            models.TaxClassCountryRate.objects.update_or_create(
                country=country_code,
                tax_class=None,
                defaults={"rate": default_rate["rate"]},
            )

        # create new instances
        to_create = [
            models.TaxClassCountryRate(
                country=country_code, tax_class_id=tax_class_id, rate=item["rate"]
            )
            for tax_class_id, item in cleaned_data.items()
            if tax_class_id not in update_tax_classes and tax_class_id is not None
        ]
        models.TaxClassCountryRate.objects.bulk_create(to_create)

    @classmethod
    def perform_mutation(cls, _root, _info, **data):
        country_code = data["country_code"]
        cleaned_data = cls.clean_input(**data)
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
