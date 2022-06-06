import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import TaxPermissions
from ....tax import error_codes, models
from ...account.enums import CountryCodeEnum
from ...core.mutations import ModelMutation
from ...core.types import Error, NonNullList
from ...core.utils import get_duplicates_items
from ..types import TaxClass
from .tax_class_create import CountryRateInput

TaxClassUpdateErrorCode = graphene.Enum.from_enum(error_codes.TaxClassUpdateErrorCode)


class TaxClassUpdateError(Error):
    code = TaxClassUpdateErrorCode(description="The error code.", required=True)
    country_codes = NonNullList(
        graphene.String,
        description="List of country codes for which the configuration is invalid.",
        required=True,
    )


class TaxClassUpdateInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the tax class.")
    update_country_rates = NonNullList(
        CountryRateInput,
        description="List of country-specific tax rates for this tax class.",
    )
    remove_country_rates = NonNullList(
        CountryCodeEnum,
        description="List of country codes for which to remove the tax class rates.",
    )


class TaxClassUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of the tax class.", required=True)
        input = TaxClassUpdateInput(
            description="Fields required to update a tax class.", required=True
        )

    class Meta:
        description = "Create a tax class."
        error_type_class = TaxClassUpdateError
        model = models.TaxClass
        object_type = TaxClass
        permissions = (TaxPermissions.MANAGE_TAXES,)

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        update_country_rates = data.get("update_country_rates", [])
        update_country_codes = [item["country_code"] for item in update_country_rates]
        remove_country_rates = data.get("remove_country_rates", [])

        if duplicated_country_codes := list(
            get_duplicates_items(update_country_codes, remove_country_rates)
        ):
            message = (
                "The same country code cannot be in both lists for updating and "
                "removing items: "
            ) + ", ".join(duplicated_country_codes)
            params = {"country_codes": duplicated_country_codes}
            code = error_codes.TaxClassUpdateErrorCode.DUPLICATED_INPUT_ITEM
            raise ValidationError(message=message, code=code, params=params)

        return super().clean_input(info, instance, data, input_cls)

    @classmethod
    def update_country_rates(cls, instance, country_rates):
        input_data_by_country = {item["country_code"]: item for item in country_rates}

        # update existing instances
        to_update = instance.country_rates.filter(
            country__in=input_data_by_country.keys()
        )
        updated_countries = []
        for obj in to_update:
            data = input_data_by_country[obj.country]
            obj.country = data["country_code"]
            obj.rate = data["rate"]
            updated_countries.append(obj.country.code)
        models.TaxClassCountryRate.objects.bulk_update(to_update, fields=("rate",))

        # create new instances
        to_create = [
            models.TaxClassCountryRate(
                tax_class=instance, country=item["country_code"], rate=item["rate"]
            )
            for item in country_rates
            if item["country_code"] not in updated_countries
        ]
        models.TaxClassCountryRate.objects.bulk_create(to_create)

    @classmethod
    def remove_country_rates(cls, country_codes):
        models.TaxClassCountryRate.objects.filter(country__in=country_codes).delete()

    @classmethod
    def save(cls, _info, instance, cleaned_input):
        instance.save()
        update_country_rates = cleaned_input.get("update_country_rates", [])
        remove_country_rates = cleaned_input.get("remove_country_rates", [])
        cls.update_country_rates(instance, update_country_rates)
        cls.remove_country_rates(remove_country_rates)
