import logging
from unittest import mock

import graphene
import pytest
from django.core.exceptions import ValidationError

from ....account.models import Address
from ....checkout import AddressType
from ....core.utils.metadata_manager import MetadataItem
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
    """Ensure invalid address creates logs when skip_validation flag = True."""
    # given
    query = ADDRESS_CREATE_MUTATION
    caplog.set_level(logging.WARNING)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = graphql_address_data_skipped_validation
    assert address_data["skipValidation"] is True
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
    assert "'postal_code': 'invalid'" in caplog.text
    assert "'country': 'IE'" in caplog.text


def test_address_validation_no_logging(
    staff_api_client,
    customer_user,
    permission_manage_users,
    graphql_address_data,
    caplog,
):
    """Ensure invalid address does not create logs when skip_validation flag = False."""
    # given
    query = ADDRESS_CREATE_MUTATION
    caplog.set_level(logging.WARNING)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = graphql_address_data
    assert not address_data.get("skipValidation")
    invalid_name = "wrong name"
    address_data["country"] = "IE"
    address_data["countryArea"] = invalid_name
    variables = {"user": user_id, "address": address_data}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["addressCreate"]
    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["field"] == "countryArea"
    assert "Invalid address input" not in caplog.text


def test_is_address_modified(address):
    # given
    address_data = {"last_name": None}
    assert address.last_name is not None

    # when
    is_modified = I18nMixin.is_address_modified(address, address_data)

    # then
    assert is_modified is True


def test_is_address_modified_no_changes_all_fields_included_in_the_input(address):
    # given
    address_data = address.as_data()
    address_data.pop("private_metadata")
    skip_validation = address_data.pop("validation_skipped")
    address_data["skip_validation"] = skip_validation

    # when
    is_modified = I18nMixin.is_address_modified(address, address_data)

    # then
    assert is_modified is False


def test_is_address_modified_no_changes_single_field_in_input(address):
    # given
    address_data = {"last_name": address.last_name}

    # when
    is_modified = I18nMixin.is_address_modified(address, address_data)

    # then
    assert is_modified is False


def test_is_address_modified_skip_validation_changed(address):
    # given
    address_data = {"skip_validation": True}
    assert address.validation_skipped is False

    # when
    is_modified = I18nMixin.is_address_modified(address, address_data)

    # then
    assert is_modified is True


def test_is_address_modified_skip_validation_not_changed(address):
    # given
    address_data = {"skip_validation": False}
    assert address.validation_skipped is False

    # when
    is_modified = I18nMixin.is_address_modified(address, address_data)

    # then
    assert is_modified is False


def test_is_address_modified_metadata_changed(address):
    # given
    key1 = "some key"
    key2 = "another key"
    value1 = "some value"
    value2 = "another value"
    address_data = {
        "metadata": [
            MetadataItem(key=key1, value=value1),
            MetadataItem(key=key2, value="new value"),
        ]
    }
    address.metadata = {key2: value2, key1: value1}
    address.save(update_fields=["metadata"])

    # when
    is_modified = I18nMixin.is_address_modified(address, address_data)

    # then
    assert is_modified is True


def test_is_address_modified_metadata_not_changed(address):
    # given
    key1 = "some key"
    key2 = "another key"
    value1 = "some value"
    value2 = "another value"
    address_data = {
        "metadata": [
            MetadataItem(key=key1, value=value1),
            MetadataItem(key=key2, value=value2),
        ]
    }
    address.metadata = {key2: value2, key1: value1}
    address.save(update_fields=["metadata"])

    # when
    is_modified = I18nMixin.is_address_modified(address, address_data)

    # then
    assert is_modified is False
