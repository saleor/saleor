import graphene
from django_countries.fields import Country

from ....permission.enums import CheckoutPermissions
from ....tax import error_codes, models
from ...account.enums import CountryCodeEnum
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_39, PREVIEW_FEATURE
from ...core.mutations import BaseMutation
from ...core.types import Error
from ..types import TaxCountryConfiguration

TaxCountryConfigurationDeleteErrorCode = graphene.Enum.from_enum(
    error_codes.TaxCountryConfigurationDeleteErrorCode
)


class TaxCountryConfigurationDeleteError(Error):
    code = TaxCountryConfigurationDeleteErrorCode(
        description="The error code.", required=True
    )


class TaxCountryConfigurationDelete(BaseMutation):
    tax_country_configuration = graphene.Field(
        TaxCountryConfiguration,
        description="Updated tax class rates grouped by a country.",
    )

    class Arguments:
        country_code = CountryCodeEnum(
            description="Country in which to update the tax class rates.", required=True
        )

    class Meta:
        description = (
            "Remove all tax class rates for a specific country."
            + ADDED_IN_39
            + PREVIEW_FEATURE
        )
        error_type_class = TaxCountryConfigurationDeleteError
        permissions = (CheckoutPermissions.MANAGE_TAXES,)

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /, **data):
        country_code = data["country_code"]
        rates = models.TaxClassCountryRate.objects.filter(country=country_code)
        rates.delete()
        country_config = TaxCountryConfiguration(
            country=Country(country_code), tax_class_country_rates=[]
        )
        return TaxCountryConfigurationDelete(tax_country_configuration=country_config)
