import pytest

from ..utils import append_klarna_data, get_price_amount, get_shopper_locale_value


@pytest.mark.parametrize(
    "language_code, shopper_locale", [("ja", "ja_JP"), ("zz", "en_US"), ("en", "en_US")]
)
def test_get_shopper_locale_value(language_code, shopper_locale, settings):
    # given
    settings.LANGUAGE_CODE = language_code

    # when
    result = get_shopper_locale_value()

    # then
    assert result == shopper_locale


def test_append_klarna_data(dummy_payment_data, payment_dummy, checkout_with_item):
    # given
    checkout_with_item.payments.add(payment_dummy)
    line = checkout_with_item.lines.first()
    payment_data = {
        "reference": "test",
    }

    # when
    append_klarna_data(dummy_payment_data, payment_data)

    # then
    total = get_price_amount(
        line.variant.price_amount * line.quantity, line.variant.currency
    )
    assert payment_data == {
        "reference": "test",
        "shopperLocale": "en_US",
        "shopperReference": dummy_payment_data.customer_email,
        "countryCode": str(checkout_with_item.country),
        "shopperEmail": dummy_payment_data.customer_email,
        "lineItems": [
            {
                "description": line.variant.product.description,
                "quantity": line.quantity,
                "id": line.variant.sku,
                "taxAmount": "0",
                "taxPercentage": 0,
                "amountExcludingTax": total,
                "amountIncludingTax": total,
            }
        ],
    }
