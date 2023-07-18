from .....account.models import Address
from ....tests.utils import get_graphql_content

MUTATION_SHOP_ADDRESS_UPDATE = """
    mutation updateShopAddress($input: AddressInput){
        shopAddressUpdate(input: $input){
            errors{
                field
                message
            }
        }
    }
"""


def test_mutation_update_company_address(
    staff_api_client,
    permission_manage_settings,
    address,
    site_settings,
):
    # given
    variables = {
        "input": {
            "streetAddress1": address.street_address_1,
            "city": address.city,
            "country": address.country.code,
            "postalCode": address.postal_code,
            "metadata": [{"key": "meta", "value": "data"}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_SHOP_ADDRESS_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )

    # then
    content = get_graphql_content(response)
    assert "errors" not in content["data"]

    site_settings.refresh_from_db()
    assert site_settings.company_address
    assert site_settings.company_address.street_address_1 == address.street_address_1
    assert site_settings.company_address.city == address.city
    assert site_settings.company_address.country.code == address.country.code
    assert site_settings.company_address.metadata == {"meta": "data"}


def test_mutation_update_company_address_remove_address(
    staff_api_client, permission_manage_settings, site_settings, address
):
    # given
    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])
    variables = {"input": None}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_SHOP_ADDRESS_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )

    # then
    content = get_graphql_content(response)
    assert "errors" not in content["data"]

    site_settings.refresh_from_db()
    assert not site_settings.company_address
    assert not Address.objects.filter(pk=address.pk).exists()


def test_mutation_update_company_address_remove_address_without_address(
    staff_api_client, permission_manage_settings, site_settings
):
    # given
    variables = {"input": None}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_SHOP_ADDRESS_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )

    # then
    content = get_graphql_content(response)
    assert "errors" not in content["data"]

    site_settings.refresh_from_db()
    assert not site_settings.company_address
