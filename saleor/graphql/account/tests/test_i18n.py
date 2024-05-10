from unittest import mock

import graphene
import pytest
from django.core.exceptions import ValidationError

from ....checkout import AddressType
from ...tests.utils import get_graphql_content
from ..i18n import I18nMixin


def test_validate_address():
    # given
    address_data = {
        "first_name": "John Saleor",
        "last_name": "Doe Mirumee",
        "company_name": "Mirumee Software",
        "street_address_1": "Tęczowa 7",
        "street_address_2": "",
        "postal_code": "53-601",
        "country": "PL",
        "city": "Wrocław",
        "country_area": "",
        "phone": "+48321321888",
    }
    # when
    address = I18nMixin.validate_address(
        address_data, address_type=AddressType.SHIPPING
    )

    # then
    assert address


def test_validate_address_invalid_postal_code():
    # given
    address_data = {
        "first_name": "John Saleor",
        "last_name": "Doe Mirumee",
        "company_name": "Mirumee Software",
        "street_address_1": "Tęczowa 7",
        "street_address_2": "",
        "postal_code": "Test Test 111 Test Road  BEDFORD  AM23 0UP",
        "country": "PL",
        "city": "Wrocław",
        "country_area": "",
        "phone": "+48321321888",
    }

    # when
    with pytest.raises(ValidationError) as error:
        I18nMixin.validate_address(address_data, address_type=AddressType.SHIPPING)

    # then
    assert len(error.value.error_dict["postal_code"]) == 2


def test_validate_address_no_country_code():
    # given
    address_data = {
        "first_name": "John Saleor",
        "last_name": "Doe Mirumee",
        "company_name": "Mirumee Software",
        "street_address_1": "Tęczowa 7",
        "street_address_2": "",
        "postal_code": "53-601",
        "country": "",
        "city": "Wrocław",
        "country_area": "",
        "phone": "+48321321888",
    }

    # when
    with pytest.raises(ValidationError) as error:
        I18nMixin.validate_address(address_data, address_type=AddressType.SHIPPING)

    # then
    assert len(error.value.error_dict["country"]) == 1


def test_validate_address_no_city():
    # given
    address_data = {
        "first_name": "John Saleor",
        "last_name": "Doe Mirumee",
        "company_name": "Mirumee Software",
        "street_address_1": "Tęczowa 7",
        "street_address_2": "",
        "postal_code": "53-601",
        "country": "PL",
        "city": "",
        "country_area": "",
        "phone": "+48321321888",
    }

    # when
    with pytest.raises(ValidationError) as error:
        I18nMixin.validate_address(address_data, address_type=AddressType.SHIPPING)

    # then
    assert len(error.value.error_dict["city"]) == 1


ADDRESS_CREATE_MUTATION = """
    mutation CreateUserAddress($user: ID!, $address: AddressInput!) {
        addressCreate(userId: $user, input: $address) {
            errors {
                field
                code
                message
            }
            address {
                city
            }
        }
    }
"""


@mock.patch("saleor.graphql.account.i18n.SKIP_ADDRESS_VALIDATION_PERMISSION_MAP", {})
def test_skip_address_validation_mutation_not_supported(
    staff_api_client,
    customer_user,
    graphql_address_data_skipped_validation,
    permission_manage_users,
):
    # given
    query = ADDRESS_CREATE_MUTATION
    address_data = graphql_address_data_skipped_validation
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    wrong_postal_code = "wrong postal code"
    address_data["postalCode"] = wrong_postal_code
    variables = {"user": user_id, "address": address_data}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["addressCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "skipValidation"
    assert errors[0]["code"] == "INVALID"
    assert (
        errors[0]["message"]
        == "This mutation doesn't allow to skip address validation."
    )
