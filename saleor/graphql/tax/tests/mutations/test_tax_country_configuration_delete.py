from .....tax.models import TaxClass
from ....tests.utils import assert_no_permission, get_graphql_content
from ..fragments import TAX_COUNTRY_CONFIGURATION_FRAGMENT

MUTATION = (
    """
    mutation TaxCountryConfigurationDelete($countryCode: CountryCode!) {
        taxCountryConfigurationDelete(countryCode: $countryCode) {
            errors {
                field
                message
                code
            }
            taxCountryConfiguration {
                ...TaxCountryConfiguration
            }
        }
    }
    """
    + TAX_COUNTRY_CONFIGURATION_FRAGMENT
)


def _test_no_permissions(api_client):
    # given
    country_code = "PL"

    # when
    response = api_client.post_graphql(
        MUTATION, {"countryCode": country_code}, permissions=[]
    )

    # then
    assert_no_permission(response)


def test_no_permission_staff(staff_api_client):
    _test_no_permissions(staff_api_client)


def test_no_permission_app(app_api_client):
    _test_no_permissions(app_api_client)


def _test_delete_tax_rates_for_country(api_client, permission_manage_taxes):
    # given
    country_code = "PL"
    tax_class_1 = TaxClass.objects.create(name="Books")
    tax_class_2 = TaxClass.objects.create(name="Accessories")
    tax_class_1.country_rates.create(country=country_code, rate=23)
    tax_class_2.country_rates.create(country=country_code, rate=23)

    # when
    response = api_client.post_graphql(
        MUTATION, {"countryCode": country_code}, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxCountryConfigurationDelete"]
    assert not data["errors"]
    assert len(data["taxCountryConfiguration"]["taxClassCountryRates"]) == 0


def test_delete_tax_rates_for_country_by_staff(
    staff_api_client, permission_manage_taxes
):
    _test_delete_tax_rates_for_country(staff_api_client, permission_manage_taxes)


def test_delete_tax_rates_for_country_by_app(app_api_client, permission_manage_taxes):
    _test_delete_tax_rates_for_country(app_api_client, permission_manage_taxes)
