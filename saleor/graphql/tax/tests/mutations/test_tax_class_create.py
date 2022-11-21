from ....tests.utils import assert_no_permission, get_graphql_content
from ..fragments import TAX_CLASS_FRAGMENT

MUTATION = (
    """
    mutation TaxClassCreate($input: TaxClassCreateInput!) {
        taxClassCreate(input: $input) {
            errors {
                field
                message
                code
                countryCodes
            }
            taxClass {
                ...TaxClass
            }
        }
    }
"""
    + TAX_CLASS_FRAGMENT
)


def _test_no_permissions(api_client):
    # given
    variables = {"input": {"name": "Test"}}

    # when
    response = api_client.post_graphql(MUTATION, variables, permissions=[])

    # then
    assert_no_permission(response)


def test_no_permission_staff(staff_api_client):
    _test_no_permissions(staff_api_client)


def test_no_permission_app(app_api_client):
    _test_no_permissions(app_api_client)


def _test_tax_class_create(api_client, permission_manage_taxes):
    # given
    name = "New tax class"
    rate = 23
    country_code = "PL"
    variables = {
        "input": {
            "name": name,
            "createCountryRates": [
                {"countryCode": country_code, "rate": rate},
            ],
        },
    }

    # when
    response = api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxClassCreate"]
    assert not data["errors"]
    assert data["taxClass"]["name"] == name
    assert len(data["taxClass"]["countries"]) == 1
    assert data["taxClass"]["countries"][0]["rate"] == rate
    assert data["taxClass"]["countries"][0]["country"]["code"] == country_code


def test_create_as_staff(staff_api_client, permission_manage_taxes):
    _test_tax_class_create(staff_api_client, permission_manage_taxes)


def test_create_as_app(app_api_client, permission_manage_taxes):
    _test_tax_class_create(app_api_client, permission_manage_taxes)
