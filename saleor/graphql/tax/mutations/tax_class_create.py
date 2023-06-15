import graphene

from ....permission.enums import CheckoutPermissions
from ....tax import error_codes, models
from ...account.enums import CountryCodeEnum
from ...core.descriptions import ADDED_IN_39
from ...core.doc_category import DOC_CATEGORY_TAXES
from ...core.mutations import ModelMutation
from ...core.types import BaseInputObjectType, Error, NonNullList
from ..types import TaxClass

TaxClassCreateErrorCode = graphene.Enum.from_enum(error_codes.TaxClassCreateErrorCode)
TaxClassCreateErrorCode.doc_category = DOC_CATEGORY_TAXES


class TaxClassCreateError(Error):
    code = TaxClassCreateErrorCode(description="The error code.", required=True)
    country_codes = NonNullList(
        graphene.String,
        description="List of country codes for which the configuration is invalid.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_TAXES


class CountryRateInput(BaseInputObjectType):
    country_code = CountryCodeEnum(
        description="Country in which this rate applies.", required=True
    )
    rate = graphene.Float(
        description=(
            "Tax rate value provided as percentage. Example: provide `23` to "
            "represent `23%` tax rate."
        ),
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_TAXES


class TaxClassCreateInput(BaseInputObjectType):
    name = graphene.String(description="Name of the tax class.", required=True)
    create_country_rates = NonNullList(
        CountryRateInput,
        description="List of country-specific tax rates to create for this tax class.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_TAXES


class TaxClassCreate(ModelMutation):
    class Arguments:
        input = TaxClassCreateInput(
            description="Fields required to create a tax class.", required=True
        )

    class Meta:
        description = "Create a tax class." + ADDED_IN_39
        error_type_class = TaxClassCreateError
        model = models.TaxClass
        object_type = TaxClass
        permissions = (CheckoutPermissions.MANAGE_TAXES,)

    @classmethod
    def create_country_rates(cls, instance, country_rates):
        to_create = [
            models.TaxClassCountryRate(
                tax_class=instance, country=item["country_code"], rate=item["rate"]
            )
            for item in country_rates
        ]
        models.TaxClassCountryRate.objects.bulk_create(to_create)

    @classmethod
    def save(cls, _info, instance, cleaned_input):
        instance.save()
        create_country_rates = cleaned_input.get("create_country_rates", [])
        cls.create_country_rates(instance, create_country_rates)
