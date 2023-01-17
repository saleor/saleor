import json
import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import Adyen
import opentracing
import opentracing.tags
from Adyen.httpclient import HTTPClient
from django.conf import settings
from django_countries.fields import Country
from requests.exceptions import ConnectTimeout

from .....checkout.calculations import (
    checkout_line_unit_price,
    checkout_shipping_price,
    checkout_total,
)
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....checkout.utils import get_or_create_checkout_metadata, is_shipping_required
from .....discount.utils import fetch_active_discounts
from .....payment.models import Payment
from .....plugins.manager import get_plugins_manager
from .... import PaymentError
from ....interface import GatewayConfig, PaymentMethodInfo
from ....utils import price_to_minor_unit

if TYPE_CHECKING:
    from ....interface import AddressData, PaymentData

logger = logging.getLogger(__name__)


# https://docs.adyen.com/checkout/payment-result-codes
FAILED_STATUSES = ["refused", "error", "cancelled"]
PENDING_STATUSES = ["pending", "received"]
AUTH_STATUS = "authorised"
HTTP_TIMEOUT = 20  # in seconds


def initialize_adyen_client(config: GatewayConfig) -> Adyen.Adyen:
    api_key = config.connection_params["api_key"]

    live_endpoint = config.connection_params.get("live")
    platform = "live" if live_endpoint else "test"
    adyen = Adyen.Adyen(
        xapikey=api_key, live_endpoint_prefix=live_endpoint, platform=platform
    )
    init_http_client(adyen)
    return adyen


def init_http_client(adyen: Adyen.Adyen):
    adyen_client = adyen.client
    adyen_client.http_client = HTTPClient(
        user_agent_suffix=adyen_client.USER_AGENT_SUFFIX,
        lib_version=adyen_client.LIB_VERSION,
        force_request=adyen_client.http_force,
        timeout=HTTP_TIMEOUT,
    )
    adyen_client.http_init = True


def get_tax_percentage_in_adyen_format(total_gross, total_net):
    tax_percentage_in_adyen_format = 0
    if total_gross and total_net:
        # get tax percent in adyen format
        gross_percentage = total_gross / total_net
        gross_percentage = gross_percentage.quantize(Decimal(".01"))  # 1.23
        tax_percentage = gross_percentage * 100 - 100  # 23.00
        tax_percentage_in_adyen_format = int(tax_percentage * 100)  # 2300
    return tax_percentage_in_adyen_format


def api_call(
    request_data: Optional[Dict[str, Any]], method: Callable, **kwargs
) -> Adyen.Adyen:
    try:
        return method(request_data, **kwargs)
    except (Adyen.AdyenError, ValueError, TypeError, ConnectTimeout) as e:
        logger.warning(f"Unable to process the payment: {e}")
        raise PaymentError(f"Unable to process the payment request: {e}.")


def prepare_address_request_data(address: Optional["AddressData"]) -> Optional[dict]:
    """Create address structure for Adyen request.

    The sample recieved from Adyen team:

    Customer enters only address 1: 2500 Valley Creek Way
    Ideal: houseNumberOrName: "2500", street: "Valley Creek Way"
    If above not possible: houseNumberOrName: "", street: "2500 Valley Creek Way"

    ***Note the blank string above

    Customer enters address 1 and address 2: 30 Granger Circle, 160 Bath Street
    Ideal: houseNumberOrName: "30 Granger Circle", street: "160 Bath Street"
    """
    house_number_or_name = ""
    if not address:
        return None

    city = address.city or address.country_area or "ZZ"
    country = str(address.country) if address.country else "ZZ"
    postal_code = address.postal_code or "ZZ"
    state_or_province = address.country_area or "ZZ"

    if address.company_name:
        house_number_or_name = address.company_name
        street = address.street_address_1
        if address.street_address_2:
            street += f" {address.street_address_2}"
    elif address.street_address_2:
        street = address.street_address_2
        house_number_or_name = address.street_address_1
    else:
        street = address.street_address_1

    return {
        "city": city,
        "country": country,
        "houseNumberOrName": house_number_or_name,
        "postalCode": postal_code,
        "stateOrProvince": state_or_province,
        "street": street,
    }


def request_data_for_payment(
    payment_information: "PaymentData",
    return_url: str,
    merchant_account: str,
    native_3d_secure: bool,
) -> Dict[str, Any]:
    payment_data = payment_information.data or {}

    if not payment_data.pop("is_valid", True):
        raise PaymentError("Payment data are not valid.")

    extra_request_params = {}
    channel = payment_data.get("channel", "web")
    origin_url = payment_data.get("originUrl")

    browser_info = payment_data.get("browserInfo")
    if browser_info:
        extra_request_params["browserInfo"] = browser_info

    billing_address = payment_data.get("billingAddress")
    if billing_address:
        extra_request_params["billingAddress"] = billing_address
    elif billing_address := prepare_address_request_data(payment_information.billing):
        extra_request_params["billingAddress"] = billing_address

    delivery_address = payment_data.get("deliveryAddress")
    if delivery_address:
        extra_request_params["deliveryAddress"] = delivery_address
    elif delivery_address := prepare_address_request_data(payment_information.shipping):
        extra_request_params["deliveryAddress"] = delivery_address

    shopper_ip = payment_data.get("shopperIP")
    if shopper_ip:
        extra_request_params["shopperIP"] = shopper_ip

    device_fingerprint = payment_data.get("deviceFingerprint")
    if device_fingerprint:
        extra_request_params["deviceFingerprint"] = device_fingerprint

    if channel.lower() == "web" and origin_url:
        extra_request_params["origin"] = origin_url

    shopper_name = payment_data.get("shopperName")
    if shopper_name:
        extra_request_params["shopperName"] = shopper_name

    extra_request_params["channel"] = channel

    payment_method = payment_data.get("paymentMethod")
    if not payment_method:
        raise PaymentError("Unable to find the paymentMethod section.")

    method = payment_method.get("type", "")
    if native_3d_secure and "scheme" == method:
        extra_request_params["additionalData"] = {"allow3DS2": "true"}

    extra_request_params["shopperEmail"] = payment_information.customer_email

    if payment_information.billing:
        extra_request_params["shopperName"] = {
            "firstName": payment_information.billing.first_name,
            "lastName": payment_information.billing.last_name,
        }
    request_data = {
        "amount": {
            "value": price_to_minor_unit(
                payment_information.amount, payment_information.currency
            ),
            "currency": payment_information.currency,
        },
        "reference": payment_information.graphql_payment_id,
        "paymentMethod": payment_method,
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        "shopperEmail": payment_information.customer_email,
        "shopperReference": payment_information.customer_email,
        **extra_request_params,
    }

    methods_that_require_checkout_details = ["afterpaytouch", "clearpay"]
    # klarna in method - because there is a lot of variable klarna methods - like pay
    # later with klarna or pay with klarna etc
    if "klarna" in method or method in methods_that_require_checkout_details:
        # Some payment methods like afterpay or klarna, requires more context for
        # processing a payment. If user pick up such payment method we add more
        # checkout details to request
        request_data = append_checkout_details(payment_information, request_data)
    return request_data


def get_shipping_data(manager, checkout_info, lines, discounts):
    address = checkout_info.shipping_address or checkout_info.billing_address
    currency = checkout_info.checkout.currency
    shipping_total = checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    total_gross = shipping_total.gross.amount
    total_net = shipping_total.net.amount
    tax_amount = shipping_total.tax.amount
    tax_percentage_in_adyen_format = get_tax_percentage_in_adyen_format(
        total_gross, total_net
    )
    return {
        "quantity": 1,
        "amountExcludingTax": price_to_minor_unit(total_net, currency),
        "taxPercentage": tax_percentage_in_adyen_format,
        "description": (
            f"Shipping - {checkout_info.delivery_method_info.delivery_method.name}"
        ),
        "id": f"Shipping:{checkout_info.delivery_method_info.delivery_method.id}",
        "taxAmount": price_to_minor_unit(tax_amount, currency),
        "amountIncludingTax": price_to_minor_unit(total_gross, currency),
    }


def append_checkout_details(payment_information: "PaymentData", payment_data: dict):
    checkout = (
        Checkout.objects.prefetch_related(
            "shipping_method",
        )
        .filter(payments__id=payment_information.payment_id)
        .first()
    )

    if not checkout:
        raise PaymentError("Unable to calculate products for klarna.")

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    discounts = fetch_active_discounts()
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
    currency = payment_information.currency
    country_code = checkout.get_country()

    payment_data["shopperLocale"] = get_shopper_locale_value(country_code)
    payment_data["countryCode"] = country_code

    line_items = []
    for line_info in lines:
        unit_price = checkout_line_unit_price(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            checkout_line_info=line_info,
            discounts=discounts,
        )
        unit_gross = unit_price.gross.amount
        unit_net = unit_price.net.amount
        tax_amount = unit_price.tax.amount
        tax_percentage_in_adyen_format = get_tax_percentage_in_adyen_format(
            unit_gross, unit_net
        )

        line_data = {
            "quantity": line_info.line.quantity,
            "amountExcludingTax": price_to_minor_unit(unit_net, currency),
            "taxPercentage": tax_percentage_in_adyen_format,
            "description": (
                f"{line_info.variant.product.name}, {line_info.variant.name}"
            ),
            "id": line_info.variant.sku or line_info.variant.get_global_id(),
            "taxAmount": price_to_minor_unit(tax_amount, currency),
            "amountIncludingTax": price_to_minor_unit(unit_gross, currency),
        }
        line_items.append(line_data)

    if checkout_info.delivery_method_info.delivery_method and is_shipping_required(
        lines
    ):
        line_items.append(get_shipping_data(manager, checkout_info, lines, discounts))

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
    manager = get_plugins_manager()
    address = checkout.billing_address or checkout.shipping_address
    discounts = fetch_active_discounts()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
    total = checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    )

    country = address.country if address else None
    if country:
        country_code = country.code
    else:
        country_code = Country(settings.DEFAULT_COUNTRY).code
    channel = get_or_create_checkout_metadata(checkout).get_value_from_metadata(
        "channel", "web"
    )
    return {
        "merchantAccount": merchant_account,
        "countryCode": country_code,
        "channel": channel,
        "amount": {
            "value": price_to_minor_unit(total.gross.amount, checkout.currency),
            "currency": checkout.currency,
        },
    }


def request_for_payment_refund(
    amount: Decimal,
    currency: str,
    graphql_payment_id: str,
    merchant_account: str,
    token: str,
) -> Dict[str, Any]:
    return {
        "merchantAccount": merchant_account,
        "modificationAmount": {
            "value": price_to_minor_unit(amount, currency),
            "currency": currency,
        },
        "originalReference": token,
        "reference": graphql_payment_id,
    }


def request_for_payment_capture(
    payment_information: "PaymentData", merchant_account: str, token: str
) -> Dict[str, Any]:
    return {
        "merchantAccount": merchant_account,
        "modificationAmount": {
            "value": price_to_minor_unit(
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


def call_refund(
    amount: Decimal,
    currency: str,
    graphql_payment_id: str,
    merchant_account: str,
    token: str,
    adyen_client: Adyen.Adyen,
):
    request = request_for_payment_refund(
        amount,
        currency,
        graphql_payment_id,
        merchant_account=merchant_account,
        token=token,
    )
    with opentracing.global_tracer().start_active_span("adyen.payment.refund") as scope:
        span = scope.span
        span.set_tag(opentracing.tags.COMPONENT, "payment")
        span.set_tag("service.name", "adyen")
        return api_call(request, adyen_client.payment.refund)


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
    with opentracing.global_tracer().start_active_span(
        "adyen.payment.capture"
    ) as scope:
        span = scope.span
        span.set_tag(opentracing.tags.COMPONENT, "payment")
        span.set_tag("service.name", "adyen")
        return api_call(request, adyen_client.payment.capture)


def request_for_payment_cancel(
    payment_information: "PaymentData",
    merchant_account: str,
    token: str,
):
    return {
        "merchantAccount": merchant_account,
        "originalReference": token,
        "reference": payment_information.graphql_payment_id,
    }


def get_payment_method_info(
    payment_information: "PaymentData", api_call_result: Adyen.Adyen
):
    additional_data = api_call_result.message.get("additionalData")
    payment_data = payment_information.data or {}
    payment_method = payment_data.get("paymentMethod", {}).get("type")
    brand = None
    if additional_data:
        brand = additional_data.get("paymentMethod")
    payment_method_info = PaymentMethodInfo(
        brand=brand,
        type="card" if payment_method == "scheme" else payment_method,
    )
    return payment_method_info


def get_request_data_for_check_payment(data: dict, merchant_account: str) -> dict:
    amount_input = data["card"].get("money")
    security_code = data["card"].get("cvc")

    request_data: Dict[str, Any] = {
        "merchantAccount": merchant_account,
        "paymentMethod": {
            "type": data["method"],
            "number": data["card"]["code"],
        },
    }

    if amount_input:
        currency = amount_input["currency"]
        value = amount_input["amount"]
        request_data["amount"] = {
            "value": price_to_minor_unit(value, currency),
            "currency": currency,
        }

    if security_code:
        request_data["paymentMethod"]["securityCode"] = security_code

    return request_data
