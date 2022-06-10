import graphene

from .....tax.error_codes import TaxCountryConfigurationUpdateErrorCode
from .....tax.models import TaxClass
from ....tests.utils import assert_no_permission, get_graphql_content
from ..fragments import TAX_COUNTRY_CONFIGURATION_FRAGMENT

MUTATION = (
    """
    mutation TaxCountryConfigurationUpdate(
        $countryCode: CountryCode!
        $updateTaxClassRates: [TaxClassRateInput!]!
    ) {
        taxCountryConfigurationUpdate(
            countryCode: $countryCode
            updateTaxClassRates: $updateTaxClassRates
        ) {
            errors {
                field
                message
                code
                taxClassIds
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
        MUTATION,
        {"countryCode": country_code, "updateTaxClassRates": []},
        permissions=[],
    )

    # then
    assert_no_permission(response)


def test_no_permission_staff(staff_api_client):
    _test_no_permissions(staff_api_client)


def test_no_permission_app(app_api_client):
    _test_no_permissions(app_api_client)


def _test_country_rates_update(api_client, permission_manage_taxes):
    # given
    tax_class_1 = TaxClass.objects.create(name="Books")
    tax_class_2 = TaxClass.objects.create(name="Accessories")
    tax_class_1.country_rates.create(country="PL", rate=23)

    id_1 = graphene.Node.to_global_id("TaxClass", tax_class_1.pk)
    id_2 = graphene.Node.to_global_id("TaxClass", tax_class_2.pk)

    # when
    variables = {
        "countryCode": "PL",
        "updateTaxClassRates": [
            {"taxClassId": id_1, "rate": 20},  # should update existing rate
            {"taxClassId": id_2, "rate": 20},  # should create new rate
        ],
    }
    response = api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxCountryConfigurationUpdate"]
    assert not data["errors"]
    assert len(data["taxCountryConfiguration"]["taxClassCountryRates"]) == 2

    response_data = []
    for item in data["taxCountryConfiguration"]["taxClassCountryRates"]:
        response_data.append({"rate": item["rate"], "id": item["taxClass"]["id"]})

    assert {"rate": 20, "id": id_1} in response_data
    assert {"rate": 20, "id": id_2} in response_data


def test_update_rates_as_staff(staff_api_client, permission_manage_taxes):
    _test_country_rates_update(staff_api_client, permission_manage_taxes)


def test_update_rates_as_app(app_api_client, permission_manage_taxes):
    _test_country_rates_update(app_api_client, permission_manage_taxes)


def test_tax_class_id_not_found(staff_api_client, permission_manage_taxes):
    # given
    TaxClass.objects.create(name="Books")

    # when
    id = "spanishinquisition"
    variables = {
        "countryCode": "PL",
        "updateTaxClassRates": [
            {"taxClassId": id, "rate": 20},
        ],
    }
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxCountryConfigurationUpdate"]
    assert data["errors"]
    assert (
        data["errors"][0]["code"]
        == TaxCountryConfigurationUpdateErrorCode.NOT_FOUND.name
    )
    assert data["errors"][0]["taxClassIds"] == [id]
