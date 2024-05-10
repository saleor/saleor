from unittest.mock import patch
from urllib.parse import urlencode

import i18naddress
import pytest
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django_countries.fields import Country

from ...order.models import Order
from .. import forms, i18n
from ..i18n_valid_address_extension import VALID_ADDRESS_EXTENSION_MAP
from ..models import User
from ..validators import validate_possible_number


@pytest.mark.parametrize("country", ["CN", "PL", "US", "IE"])
def test_address_form_for_country(country):
    # given
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "country": country,
        "phone": "123456789",
    }

    # when
    form = forms.get_address_form(data, country_code=country)
    errors = form.errors
    rules = i18naddress.get_validation_rules({"country_code": country})
    required = rules.required_fields

    # then
    if "street_address" in required:
        assert "street_address_1" in errors
    else:
        assert "street_address_1" not in errors
    if "city" in required:
        assert "city" in errors
    else:
        assert "city" not in errors
    if "city_area" in required:
        assert "city_area" in errors
    else:
        assert "city_area" not in errors
    if "country_area" in required:
        assert "country_area" in errors
    else:
        assert "country_area" not in errors
    if "postal_code" in required:
        assert "postal_code" in errors
    else:
        assert "postal_code" not in errors


def test_address_form_postal_code_validation():
    # given
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "country": "PL",
        "postal_code": "XXX",
    }

    # when
    form = forms.get_address_form(data, country_code="PL")
    errors = form.errors
    # then
    assert "postal_code" in errors


def test_address_form_long_street_address_validation():
    # given
    data = {
        "city": "test",
        "city_area": "test",
        "company_name": "test",
        "first_name": "Amelia",
        "last_name": "Doe",
        "country": "US",
        "country_area": "IN",
        "phone": "",
        "postal_code": "46802",
        "street_address_1": (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut "
            "labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
            "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit "
            "esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt "
            "in culpa qui officia deserunt mollit anim id est laborum"
        ),
    }

    # when
    form = forms.get_address_form(data, country_code="US")
    errors = form.errors

    # then
    assert "street_address_1" in errors


@pytest.mark.parametrize(
    ("country", "phone", "is_valid"),
    [
        ("US", "123-456-7890", False),
        ("US", "(541) 754-3010", True),
        ("FR", "0600000000", True),
    ],
)
def test_address_form_phone_number_validation(country, phone, is_valid):
    data = {"country": country, "phone": phone}
    form = forms.get_address_form(data, country_code="PL")
    errors = form.errors
    if not is_valid:
        assert "phone" in errors
    else:
        assert "phone" not in errors


@pytest.mark.parametrize(
    ("form_data", "form_valid", "expected_country"),
    [
        ({}, False, "PL"),
        (
            {
                "street_address_1": "Foo bar",
                "postal_code": "00-123",
                "city": "Warsaw",
            },
            True,
            "PL",
        ),
        ({"country": "US"}, False, "US"),
        (
            {
                "street_address_1": "Foo bar",
                "postal_code": "0213",
                "city": "Warsaw",
            },
            False,
            "PL",
        ),
    ],
)
def test_get_address_form(form_data, form_valid, expected_country):
    data = {"first_name": "John", "last_name": "Doe", "country": "PL"}
    data.update(form_data)
    query_dict = urlencode(data)
    form = forms.get_address_form(
        data=QueryDict(query_dict), country_code=data["country"]
    )
    assert form.is_valid() is form_valid
    assert form.i18n_country_code == expected_country


def test_get_address_form_no_country_code():
    form = forms.get_address_form(data={}, country_code=None)
    assert isinstance(form, i18n.AddressForm)


def test_country_aware_form_has_only_supported_countries():
    default_form = i18n.COUNTRY_FORMS["US"]
    instance = default_form()
    country_field = instance.fields["country"]
    country_choices = [code for code, label in country_field.choices]

    for country in i18n.UNKNOWN_COUNTRIES:
        assert country not in i18n.COUNTRY_FORMS
        assert country not in country_choices


@pytest.mark.parametrize(
    ("input_data", "is_valid"),
    [
        ({"phone": "123"}, False),
        ({"phone": "+48123456789"}, True),
        ({"phone": "+12025550169"}, True),
        ({"phone": "+481234567890"}, False),
        ({"phone": "testext"}, False),
        ({"phone": "1-541-754-3010"}, False),
        ({"phone": "001-541-754-3010"}, False),
        ({"phone": "+1-541-754-3010"}, True),
        ({"country": "US", "phone": "123-456-7890"}, False),
        ({"country": "US", "phone": "555-555-5555"}, False),
        ({"country": "US", "phone": "754-3010"}, False),
        ({"country": "US", "phone": "001-541-754-3010"}, False),
        ({"country": "US", "phone": "(541) 754-3010"}, True),
        ({"country": "US", "phone": "1-541-754-3010"}, True),
        ({"country": "FR", "phone": "1234567890"}, False),
        ({"country": "FR", "phone": "0600000000"}, True),
    ],
)
def test_validate_possible_number(input_data, is_valid):
    if not is_valid:
        with pytest.raises(ValidationError):
            validate_possible_number(**input_data)
    else:
        validate_possible_number(**input_data)


def test_address_as_data(address):
    data = address.as_data()
    assert data == {
        "first_name": "John",
        "last_name": "Doe",
        "company_name": "Mirumee Software",
        "street_address_1": "Tęczowa 7",
        "street_address_2": "",
        "city": "WROCŁAW",
        "city_area": "",
        "postal_code": "53-601",
        "country": "PL",
        "country_area": "",
        "phone": "+48713988102",
        "metadata": {},
        "private_metadata": {},
        "validation_skipped": False,
    }


def test_copy_address(address):
    copied_address = address.get_copy()
    assert copied_address.pk != address.pk
    assert copied_address == address


def test_compare_addresses_with_country_object(address):
    copied_address = address.get_copy()
    copied_address.country = Country("PL")
    copied_address.save()
    assert address == copied_address


def test_compare_addresses_different_country(address):
    copied_address = address.get_copy()
    copied_address.country = Country("FR")
    copied_address.save()
    assert address != copied_address


@pytest.mark.parametrize(
    ("email", "first_name", "last_name", "full_name"),
    [
        ("John@example.com", "John", "Doe", "John Doe"),
        ("John@example.com", "John", "", "John"),
        ("John@example.com", "", "Doe", "Doe"),
        ("John@example.com", "", "", "John@example.com"),
    ],
)
def test_get_full_name_user_with_names(
    email, first_name, last_name, full_name, address
):
    user = User(email=email, first_name=first_name, last_name=last_name)
    assert user.get_full_name() == full_name


@pytest.mark.parametrize(
    ("email", "first_name", "last_name", "full_name"),
    [
        ("John@example.com", "John", "Doe", "John Doe"),
        ("John@example.com", "John", "", "John"),
        ("John@example.com", "", "Doe", "Doe"),
        ("John@example.com", "", "", "John@example.com"),
    ],
)
def test_get_full_name_user_with_address(
    email, first_name, last_name, full_name, address
):
    address.first_name = first_name
    address.last_name = last_name
    user = User(email=email, default_billing_address=address)
    assert user.get_full_name() == full_name


@pytest.mark.parametrize(
    ("email", "first_name", "last_name", "full_name"),
    [
        ("John@example.com", "John", "Doe", "John Doe"),
        ("John@example.com", "John", "", "John"),
        ("John@example.com", "", "Doe", "Doe"),
        ("John@example.com", "", "", "Arnold Green"),
    ],
)
def test_get_full_name(email, first_name, last_name, full_name, address):
    address.first_name = "Arnold"
    address.last_name = "Green"
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        default_billing_address=address,
    )
    assert user.get_full_name() == full_name


def test_customers_doesnt_return_duplicates(customer_user, channel_USD):
    Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                channel=channel_USD,
            ),
        ]
    )
    assert User.objects.customers().count() == 1


def test_customers_show_staff_with_order(admin_user, channel_USD):
    assert User.objects.customers().count() == 0
    Order.objects.create(
        user=admin_user,
        channel=channel_USD,
    )
    assert User.objects.customers().count() == 1


@pytest.mark.parametrize(
    ("country_area_input", "country_area_output", "is_valid"),
    [
        ("Dublin", "Co. Dublin", True),
        ("Co. Dublin", "Co. Dublin", True),
        ("Dummy Area", None, False),
        ("dublin", "Co. Dublin", True),
        (" dublin ", "Co. Dublin", True),
        ("", "", True),
        (None, "", True),
    ],
)
@patch.dict(
    VALID_ADDRESS_EXTENSION_MAP,
    {"IE": {"country_area": {"dublin": "Co. Dublin"}, "city_area": {"dummy": "dummy"}}},
)
def test_substitute_invalid_values(country_area_input, country_area_output, is_valid):
    # given
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "country": "IE",
        "country_area": country_area_input,
        "city": "Dublin",
        "street_address_1": "1 Anglesea St",
        "postal_code": "D02 FK84",
    }

    # when
    form = forms.get_address_form(data, country_code="PL")
    errors = form.errors

    # then
    assert form.cleaned_data.get("country_area") == country_area_output
    if not is_valid:
        assert "country_area" in errors
    else:
        assert not errors
