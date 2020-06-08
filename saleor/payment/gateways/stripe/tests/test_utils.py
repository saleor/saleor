from decimal import Decimal
from math import isclose

from django_countries import countries

from ....interface import AddressData
from ....utils import create_payment_information
from ..utils import (
    get_amount_for_stripe,
    get_amount_from_stripe,
    get_currency_for_stripe,
    get_currency_from_stripe,
    get_payment_billing_fullname,
    shipping_to_stripe_dict,
)


def test_get_amount_for_stripe():
    assert get_amount_for_stripe(Decimal(1), "USD") == 100
    assert get_amount_for_stripe(Decimal(1), "usd") == 100

    assert get_amount_for_stripe(Decimal(0.01), "USD") == 1
    assert get_amount_for_stripe(Decimal(24.24), "USD") == 2424
    assert get_amount_for_stripe(Decimal(42.42), "USD") == 4242

    assert get_amount_for_stripe(Decimal(1), "JPY") == 1
    assert get_amount_for_stripe(Decimal(1), "jpy") == 1


def test_get_amount_from_stripe():
    assert get_amount_from_stripe(100, "USD") == Decimal(1)
    assert get_amount_from_stripe(100, "usd") == Decimal(1)

    assert isclose(get_amount_from_stripe(1, "USD"), Decimal(0.01))
    assert isclose(get_amount_from_stripe(2424, "USD"), Decimal(24.24))
    assert isclose(get_amount_from_stripe(4242, "USD"), Decimal(42.42))

    assert get_amount_from_stripe(1, "JPY") == Decimal(1)
    assert get_amount_from_stripe(1, "jpy") == Decimal(1)


def test_get_currency_for_stripe():
    assert get_currency_for_stripe("USD") == "usd"
    assert get_currency_for_stripe("usd") == "usd"
    assert get_currency_for_stripe("uSd") == "usd"


def test_get_currency_from_stripe():
    assert get_currency_from_stripe("USD") == "USD"
    assert get_currency_from_stripe("usd") == "USD"
    assert get_currency_from_stripe("uSd") == "USD"


def test_get_payment_billing_fullname(payment_dummy):
    payment_info = create_payment_information(payment_dummy)

    expected_fullname = "%s %s" % (
        payment_dummy.billing_last_name,
        payment_dummy.billing_first_name,
    )
    assert get_payment_billing_fullname(payment_info) == expected_fullname


def test_get_payment_billing_fullname_no_billing(payment_dummy):
    payment_info = create_payment_information(payment_dummy)
    payment_info.billing = None

    assert not payment_info.billing
    assert get_payment_billing_fullname(payment_info) == ""


def test_shipping_address_to_stripe_dict(address):
    address_data = AddressData(**address.as_data())
    expected_address_dict = {
        "name": "John Doe",
        "phone": "+48713988102",
        "address": {
            "line1": address.street_address_1,
            "line2": address.street_address_2,
            "city": address.city,
            "state": address.country_area,
            "postal_code": address.postal_code,
            "country": dict(countries).get(address.country, ""),
        },
    }
    assert shipping_to_stripe_dict(address_data) == expected_address_dict
