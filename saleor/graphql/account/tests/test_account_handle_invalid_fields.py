import pytest

from ....account.error_codes import AccountErrorCode
from ..mutations.account import AccountAddressCreate


def test_account_address_create_get_invalid_fields():
    invalid_input = {
        "firstName": "",
        "lastName": "Doe",
        "streetAddress1": "",
        "city": "New York",
        "postalCode": "",
    }

    invalid_fields = AccountAddressCreate.get_invalid_fields(invalid_input)
    assert len(invalid_fields) == 3
    assert "firstName" in invalid_fields
    assert "streetAddress1" in invalid_fields
    assert "postalCode" in invalid_fields

    valid_input = {
        "firstName": "John",
        "lastName": "Doe",
        "streetAddress1": "123 Main St",
        "city": "New York",
        "postalCode": "12345",
    }

    valid_fields = AccountAddressCreate.get_invalid_fields(valid_input)
    assert len(valid_fields) == 0


def test_account_address_create_handle_invalid_fields():
    invalid_fields = ["firstName", "streetAddress1", "postalCode"]

    with pytest.raises(ValueError) as error:
        AccountAddressCreate.handle_invalid_fields(invalid_fields)

    errors = error.value.args[0]
    assert len(errors) == 3

    assert errors[0].field == "firstName"
    assert errors[0].code == AccountErrorCode.INVALID.value
    assert errors[0].message == "Invalid value for field 'firstName'."

    assert errors[1].field == "streetAddress1"
    assert errors[1].code == AccountErrorCode.INVALID.value
    assert errors[1].message == "Invalid value for field 'streetAddress1'."

    assert errors[2].field == "postalCode"
    assert errors[2].code == AccountErrorCode.INVALID.value
    assert errors[2].message == "Invalid value for field 'postalCode'."
