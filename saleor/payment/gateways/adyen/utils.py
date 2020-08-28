import json
import logging
from decimal import Decimal
from typing import Any, Callable, Dict, Optional

import Adyen
from babel.numbers import get_currency_precision
from django.conf import settings
from django_countries.fields import Country

from ....checkout.calculations import checkout_line_total, checkout_total
from ....checkout.models import Checkout
from ....core.prices import quantize_price
from ....discount.utils import fetch_active_discounts
from ....payment.models import Payment
from ... import PaymentError
from ...interface import PaymentData, PaymentMethodInfo

logger = logging.getLogger(__name__)


# https://docs.adyen.com/checkout/payment-result-codes
FAILED_STATUSES = ["refused", "error", "cancelled"]
PENDING_STATUSES = ["pending", "received"]
AUTH_STATUS = "authorised"


def from_adyen_price(value: str, currency: str):
    value = Decimal(value)
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return value * number_places


def to_adyen_price(value: Decimal, currency: str):
    """Adyen doesn't use values with comma.

    Take the value, discover the precision of currency and multiply value by
    Decimal('10.0'), then change quantization to remove the comma.
    """
    value = quantize_price(value, currency=currency)
    precision = get_currency_precision(currency)
    number_places = Decimal("10.0") ** precision
    value_without_comma = value * number_places
    return str(value_without_comma.quantize(Decimal("1")))


def api_call(request_data: Optional[Dict[str, Any]], method: Callable) -> Adyen.Adyen:
    try:
        return method(request_data)
    except (Adyen.AdyenError, ValueError, TypeError) as e:
        logger.error(f"Unable to process the payment: {e}")
        raise PaymentError("Unable to process the payment request.")


def request_data_for_payment(
    payment_information: "PaymentData",
    return_url: str,
    merchant_account: str,
    origin_url: str,
) -> Dict[str, Any]:
    payment_data = payment_information.data or {}

    if not payment_data.pop("is_valid", True):
        raise PaymentError("Payment data are not valid.")

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
        and origin_url
    ):
        extra_request_params["origin"] = origin_url

    payment_method = payment_data.get("paymentMethod")
    if not payment_method:
        raise PaymentError("Unable to find the paymentMethod section.")

    request_data = {
        "amount": {
            "value": to_adyen_price(
                payment_information.amount, payment_information.currency
            ),
            "currency": payment_information.currency,
        },
        "reference": payment_information.graphql_payment_id,
        "paymentMethod": payment_method,
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        **extra_request_params,
    }

    method = payment_method.get("type", [])
    if "klarna" in method:
        request_data = append_klarna_data(payment_information, request_data)
    return request_data


def append_klarna_data(payment_information: "PaymentData", payment_data: dict):
    checkout = Checkout.objects.filter(
        payments__id=payment_information.payment_id
    ).first()

    if not checkout:
        raise PaymentError("Unable to calculate products for klarna.")

    lines = checkout.lines.prefetch_related("variant").all()
    discounts = fetch_active_discounts()
    currency = payment_information.currency
    country_code = checkout.get_country()

    payment_data["shopperLocale"] = get_shopper_locale_value(country_code)
    payment_data["shopperReference"] = payment_information.customer_email
    payment_data["countryCode"] = country_code
    payment_data["shopperEmail"] = payment_information.customer_email
    line_items = []
    for line in lines:
        total = checkout_line_total(line=line, discounts=discounts)
        total_gross = total.gross.amount
        total_net = total.net.amount
        tax_amount = total.tax.amount
        line_data = {
            "quantity": line.quantity,
            "amountExcludingTax": to_adyen_price(total_net, currency),
            "taxPercentage": round(tax_amount / total_gross * 100),
            "description": f"{line.variant.product.name}, {line.variant.name}",
            "id": line.variant.sku,
            "taxAmount": to_adyen_price(tax_amount, currency),
            "amountIncludingTax": to_adyen_price(total_gross, currency),
        }
        line_items.append(line_data)
    payment_data["lineItems"] = line_items
    return payment_data


def get_shopper_locale_value(country_code: str):
    # Remove this function when "shopperLocale" will come from frontend site
    country_code_to_shopper_locale_value = {
        # https://docs.adyen.com/checkout/components-web/
        # localization-components#change-language
        "CN": "zh_CN",
        "DK": "da_DK",
        "NL": "nl_NL",
        "US": "en_US",
        "FI": "fi_FI",
        "FR": "fr_FR",
        "DR": "de_DE",
        "IT": "it_IT",
        "JP": "ja_JP",
        "KR": "ko_KR",
        "NO": "no_NO",
        "PL": "pl_PL",
        "BR": "pt_BR",
        "RU": "ru_RU",
        "ES": "es_ES",
        "SE": "sv_SE",
    }
    return country_code_to_shopper_locale_value.get(country_code, "en_US")


def request_data_for_gateway_config(
    checkout: "Checkout", merchant_account
) -> Dict[str, Any]:
    address = checkout.billing_address or checkout.shipping_address
    discounts = fetch_active_discounts()
    lines = checkout.lines.prefetch_related("variant").all()
    total = checkout_total(checkout=checkout, lines=lines, discounts=discounts)

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
        "amount": {
            "value": to_adyen_price(total.gross.amount, checkout.currency),
            "currency": checkout.currency,
        },
    }


def request_for_payment_refund(
    payment_information: "PaymentData", merchant_account, token
) -> Dict[str, Any]:
    return {
        "merchantAccount": merchant_account,
        "modificationAmount": {
            "value": to_adyen_price(
                payment_information.amount, payment_information.currency
            ),
            "currency": payment_information.currency,
        },
        "originalReference": token,
        "reference": payment_information.graphql_payment_id,
    }


def request_for_payment_capture(
    payment_information: "PaymentData", merchant_account: str, token: str
) -> Dict[str, Any]:
    return {
        "merchantAccount": merchant_account,
        "modificationAmount": {
            "value": to_adyen_price(
                payment_information.amount, payment_information.currency
            ),
            "currency": payment_information.currency,
        },
        "originalReference": token,
        "reference": payment_information.graphql_payment_id,
    }


def update_payment_with_action_required_data(
    payment: Payment, action: dict, details: list
):
    action_required_data = {
        "payment_data": action["paymentData"],
        "parameters": [detail["key"] for detail in details],
    }
    if payment.extra_data:
        payment_extra_data = json.loads(payment.extra_data)
        try:
            payment_extra_data.append(action_required_data)
            extra_data = payment_extra_data
        except AttributeError:
            extra_data = [payment_extra_data, action_required_data]
    else:
        extra_data = [action_required_data]

    payment.extra_data = json.dumps(extra_data)
    payment.save(update_fields=["extra_data"])


def call_capture(
    payment_information: "PaymentData",
    merchant_account: str,
    token: str,
    adyen_client: Adyen.Adyen,
):
    # https://docs.adyen.com/checkout/capture#make-an-api-call-to-capture-a-payment

    request = request_for_payment_capture(
        payment_information=payment_information,
        merchant_account=merchant_account,
        token=token,
    )
    return api_call(request, adyen_client.payment.capture)


def request_for_payment_cancel(
    payment_information: "PaymentData", merchant_account: str, token: str,
):
    return {
        "merchantAccount": merchant_account,
        "originalReference": token,
        "reference": payment_information.graphql_payment_id,
    }


def get_payment_method_info(
    payment_information: "PaymentData", api_call_result: Adyen.Adyen
):
    payment_method_info = None
    additional_data = api_call_result.message.get("additionalData")
    payment_data = payment_information.data or {}
    payment_method = payment_data.get("paymentMethod", {}).get("type")
    if additional_data:
        payment_method_info = PaymentMethodInfo(
            brand=additional_data.get("paymentMethod"),
            type="card" if payment_method == "scheme" else payment_method,
        )
    return payment_method_info
