import pytest
from django.core.exceptions import ValidationError

from ....checkout import AddressType
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
