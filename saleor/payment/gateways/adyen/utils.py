import logging
from decimal import Decimal
from typing import Any, Callable, Dict

import Adyen
from babel.numbers import get_currency_precision
from django.conf import settings
from django_countries.fields import Country

from ....checkout.models import Checkout
from ....core.prices import quantize_price
from ... import PaymentError
from ...interface import PaymentData

logger = logging.getLogger(__name__)


def get_price_amount(value: Decimal, currency: str):
    """Adyen doesn't use values with comma.

    Take the value, discover the precision of currency and multiply value by
    Decimal('10.0'), then change quantization to remove the comma.
    """
    value = quantize_price(value, currency=currency)
    precision = get_currency_precision(currency)
    number_places = Decimal("10.0") ** precision
    value_without_comma = value * number_places
    return str(value_without_comma.quantize(Decimal("1")))


def api_call(requst_data: Dict[str, Any], method: Callable) -> Adyen.Adyen:
    try:
        return method(requst_data)
    except (Adyen.AdyenError, ValueError, TypeError) as e:
        logger.error(f"Unable to process the payment: {e}")
        raise PaymentError("Unable to process the payment request.")


def request_data_for_payment(
    payment_information: "PaymentData", return_url, merchant_account, origin_url
) -> Dict[str, Any]:
    payment_data = payment_information.data or {}

    if not payment_data.pop("is_valid", True):
        raise PaymentError("Payment data are not valid")

    extra_request_params = {}
    if "browserInfo" in payment_data:
        extra_request_params["browserInfo"] = payment_data["browserInfo"]
    if "billingAddress" in payment_data:
        extra_request_params["billingAddress"] = payment_data["billingAddress"]
    if "shopperIP" in payment_data:
        extra_request_params["shopperIP"] = payment_data["shopperIP"]
    if (
        "browserInfo" in extra_request_params
        and "billingAddress" in extra_request_params
    ):
        # Replace this assigment. Add note that customer_ip_address has incorrect name
        # Add to dashboard config the flow to combine channel with url like:
        # web1:https://shop.com, web2:https://shop1.com
        extra_request_params["origin"] = origin_url
    print(
        float(quantize_price(payment_information.amount, payment_information.currency))
    )
    request = {
        "amount": {
            "value": get_price_amount(
                payment_information.amount, payment_information.currency
            ),
            "currency": payment_information.currency,
        },
        "reference": payment_information.payment_id,
        "paymentMethod": payment_data["paymentMethod"],
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        **extra_request_params,
    }
    return request


def request_data_for_gateway_config(
    checkout: "Checkout", merchant_account
) -> Dict[str, str]:
    address = checkout.billing_address or checkout.shipping_address

    # FIXME check how it works if we have None here
    country = address.country if address else None
    if country:
        country_code = country.code
    else:
        country_code = Country(settings.DEFAULT_COUNTRY).code
    channel = checkout.get_value_from_metadata("channel", "web")
    return {
        "merchantAccount": merchant_account,
        "countryCode": country_code,
        "channel": channel,
    }


def request_for_payment_refund(
    payment_information: "PaymentData", merchant_account, token
) -> Dict[str, Any]:
    return {
        "merchantAccount": merchant_account,
        "modificationAmount": {
            "value": get_price_amount(
                payment_information.amount, payment_information.currency
            ),
            "currency": payment_information.currency,
        },
        "originalReference": token,
        "reference": payment_information.payment_id,
    }
