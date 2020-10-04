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
    assert get_amount_for_stripe(Decimal(1), "EUR") == 100
    assert get_amount_for_stripe(Decimal(1), "EUR") == 100

    assert get_amount_for_stripe(Decimal(0.01), "EUR") == 1
    assert get_amount_for_stripe(Decimal(24.24), "EUR") == 2424
    assert get_amount_for_stripe(Decimal(42.42), "EUR") == 4242

    assert get_amount_for_stripe(Decimal(1), "JPY") == 1
    assert get_amount_for_stripe(Decimal(1), "jpy") == 1


def test_get_amount_from_stripe():
    assert get_amount_from_stripe(100, "EUR") == Decimal(1)
    assert get_amount_from_stripe(100, "EUR") == Decimal(1)

    assert isclose(get_amount_from_stripe(1, "EUR"), Decimal(0.01))
    assert isclose(get_amount_from_stripe(2424, "EUR"), Decimal(24.24))
    assert isclose(get_amount_from_stripe(4242, "EUR"), Decimal(42.42))

    assert get_amount_from_stripe(1, "JPY") == Decimal(1)
    assert get_amount_from_stripe(1, "jpy") == Decimal(1)


def test_get_currency_for_stripe():
    assert get_currency_for_stripe("EUR") == "EUR"
    assert get_currency_for_stripe("EUR") == "EUR"
    assert get_currency_for_stripe("EUR") == "EUR"


def test_get_currency_from_stripe():
    assert get_currency_from_stripe("EUR") == "EUR"
    assert get_currency_from_stripe("EUR") == "EUR"
    assert get_currency_from_stripe("EUR") == "EUR"


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
