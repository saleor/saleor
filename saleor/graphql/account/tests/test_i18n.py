import logging
from unittest import mock

import graphene
import pytest
from django.core.exceptions import ValidationError

from ....account.models import Address
from ....checkout import AddressType
from ...tests.utils import get_graphql_content
from ..i18n import I18nMixin

logger = logging.getLogger(__name__)


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
                id
                city
                postalCode
                phone
                country {
                    code
                }
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


def test_skip_validation_multiple_invalid_fields(
    staff_api_client,
    customer_user,
    permission_manage_users,
):
    # given
    query = ADDRESS_CREATE_MUTATION
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    invalid_name = "invalid name"
    address_data = {
        "firstName": invalid_name,
        "lastName": invalid_name,
        "companyName": invalid_name,
        "streetAddress1": invalid_name,
        "streetAddress2": invalid_name,
        "postalCode": invalid_name,
        "country": "US",
        "city": invalid_name,
        "countryArea": invalid_name,
        "metadata": [{"key": "public", "value": "public_value"}],
        "skipValidation": True,
    }
    variables = {"user": user_id, "address": address_data}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["addressCreate"]
    assert not data["errors"]
    assert data["address"]["country"]["code"] == "US"
    assert data["address"]["postalCode"] == invalid_name
    db_address = Address.objects.get(first_name=invalid_name)
    assert db_address.postal_code == invalid_name
    assert db_address.country_area == invalid_name
    assert db_address.city == invalid_name
    assert db_address.validation_skipped is True


@pytest.mark.parametrize("street", [None, "", " "])
def test_skip_address_validation_missing_required_fields(
    street,
    staff_api_client,
    customer_user,
    permission_manage_users,
    graphql_address_data_skipped_validation,
):
    # given
    query = ADDRESS_CREATE_MUTATION
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = graphql_address_data_skipped_validation
    address_data["streetAddress1"] = street
    variables = {"user": user_id, "address": address_data}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["addressCreate"]
    assert not data["address"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "streetAddress1"
    assert errors[0]["code"] == "REQUIRED"


def test_skip_address_validation_with_correct_input_run_normalization(
    staff_api_client,
    customer_user,
    permission_manage_users,
    graphql_address_data_skipped_validation,
):
    # given
    query = ADDRESS_CREATE_MUTATION
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = graphql_address_data_skipped_validation
    variables = {"user": user_id, "address": address_data}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["addressCreate"]
    assert not data["errors"]
    assert data["address"]["city"] != address_data["city"]
    assert data["address"]["city"] == address_data["city"].upper()
    global_id = data["address"]["id"]
    _, id = graphene.Node.from_global_id(global_id)
    address_db = Address.objects.get(id=id)
    assert address_db.city != address_data["city"]
    assert address_db.city == address_data["city"].upper()
    assert address_db.validation_skipped is False


def test_skip_address_validation_with_incorrect_input_skip_normalization(
    staff_api_client,
    customer_user,
    permission_manage_users,
    graphql_address_data_skipped_validation,
):
    # given
    query = ADDRESS_CREATE_MUTATION
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = graphql_address_data_skipped_validation
    invalid_name = "invalid name"
    address_data["postalCode"] = invalid_name
    variables = {"user": user_id, "address": address_data}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["addressCreate"]
    assert not data["errors"]
    assert data["address"]["city"] != address_data["city"].upper()
    assert data["address"]["city"] == address_data["city"]
    assert data["address"]["postalCode"] == invalid_name
    global_id = data["address"]["id"]
    _, id = graphene.Node.from_global_id(global_id)
    address_db = Address.objects.get(id=id)
    assert address_db.city != address_data["city"].upper()
    assert address_db.city == address_data["city"]
    assert address_db.postal_code == invalid_name
    assert address_db.validation_skipped is True


def test_skip_address_validation_logging(
    staff_api_client,
    customer_user,
    permission_manage_users,
    graphql_address_data_skipped_validation,
    caplog,
):
    # given
    query = ADDRESS_CREATE_MUTATION
    caplog.set_level(logging.WARNING)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = graphql_address_data_skipped_validation
    invalid_name = "wrong name"
    address_data["country"] = "IE"
    address_data["postalCode"] = invalid_name
    address_data["countryArea"] = invalid_name
    variables = {"user": user_id, "address": address_data}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["addressCreate"]
    assert not data["errors"]
    assert "'country_area': 'wrong name'" in caplog.text
    assert "'postal_code': 'wrong name'" in caplog.text
    assert "'skip_validation': True" in caplog.text
    assert "'country': 'IE'" in caplog.text
