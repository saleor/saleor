import logging
from typing import Iterable, Optional

import requests
from django.utils import timezone
from posuto import Posuto
from requests.auth import HTTPBasicAuth

from saleor.order.models import Fulfillment

from ... import PaymentError
from ...interface import AddressData, PaymentData
from ...models import Payment
from ...utils import price_to_minor_unit
from .api_types import ApiConfig, PaymentResult, PaymentStatus
from .const import NP_ATOBARAI, NP_TEST_URL, NP_URL
from .errors import (
    FULFILLMENT_REPORT_RESULT_ERRORS,
    TRANSACTION_CANCELLATION_RESULT_ERROR,
    TRANSACTION_REGISTRATION_RESULT_ERRORS,
    get_error_messages_from_codes,
    get_reason_messages_from_codes,
)

REQUEST_TIMEOUT = 15


logger = logging.getLogger(__name__)


def get_url(config: ApiConfig, path: str = "") -> str:
    """Resolve test/production URLs based on the api config."""
    return f"{(NP_TEST_URL if config.test_mode else NP_URL)}{path}"


def _request(
    config: ApiConfig,
    method: str,
    path: str = "",
    json: Optional[dict] = None,
) -> requests.Response:
    return requests.request(
        method=method,
        url=get_url(config, path),
        timeout=REQUEST_TIMEOUT,
        json=json or {},
        auth=HTTPBasicAuth(config.merchant_code, config.sp_code),
        headers={"X-NP-Terminal-Id": config.terminal_id},
    )


def np_request(
    config: ApiConfig, method: str, path: str = "", json: Optional[dict] = None
) -> requests.Response:
    try:
        response = _request(config, method, path, json)
        # NP responses with status code 400 should be processed by api functions
        # They contain error details that we need to pass to the customer
        if 400 < response.status_code <= 600:
            raise requests.HTTPError
        return response
    except requests.RequestException:
        raise PaymentError("Cannot connect to NP Atobarai.")


def health_check(config: ApiConfig) -> bool:
    try:
        response = _request(config, "post", "/authorizations/find")
        return response.status_code not in [401, 403]
    except requests.HTTPError:
        return False


def _format_name(ad: AddressData):
    """Follow the Japanese name guidelines."""
    return f"{ad.first_name} {ad.last_name}".strip()


def _format_address(config: ApiConfig, ad: AddressData):
    """Follow the Japanese address guidelines."""
    # example: "東京都千代田区麹町４－２－６　住友不動産麹町ファーストビル５階"
    if not config.fill_missing_address:
        return f"{ad.country_area}" f"{ad.street_address_2}" f"{ad.street_address_1}"
    with Posuto() as pp:
        try:
            jap_ad = pp.get(ad.postal_code)
        except KeyError:
            raise PaymentError(
                "Valid Japanese address is required for transaction in NP Atobarai."
            )
        else:
            return (
                f"{ad.country_area}"
                f"{jap_ad.city}"
                f"{jap_ad.neighborhood}"
                f"{ad.street_address_2}"
                f"{ad.street_address_1}"
            )


def register_transaction(
    config: ApiConfig, payment_information: "PaymentData"
) -> PaymentResult:
    order_date = timezone.now().strftime("%Y-%m-%d")

    billing = payment_information.billing
    shipping = payment_information.shipping

    if not billing:
        raise PaymentError(
            "Billing address is required for transaction in NP Atobarai."
        )
    if not shipping:
        raise PaymentError(
            "Shipping address is required for transaction in NP Atobarai."
        )

    data = {
        "transactions": [
            {
                "shop_transaction_id": payment_information.payment_id,
                "shop_order_date": order_date,
                "settlement_type": NP_ATOBARAI,
                "billed_amount": int(
                    price_to_minor_unit(
                        payment_information.amount, payment_information.currency
                    )
                ),
                "customer": {
                    "customer_name": billing.first_name,
                    "company_name": billing.company_name,
                    "zip_code": billing.postal_code,
                    "address": _format_address(config, billing),
                    "tel": billing.phone.replace("+81", "0"),
                    "email": payment_information.customer_email,
                },
                "dest_customer": {
                    "customer_name": _format_name(shipping),
                    "company_name": shipping.company_name,
                    "zip_code": shipping.postal_code,
                    "address": _format_address(config, shipping),
                    "tel": shipping.phone.replace("+81", "0"),
                },
                "goods": [
                    {
                        "quantity": line.quantity,
                        "goods_name": line.product_name,
                        "goods_price": int(
                            price_to_minor_unit(
                                line.gross, payment_information.currency
                            )
                        ),
                    }
                    for line in payment_information.lines
                ],
            },
        ]
    }

    response = np_request(config, "post", "/transactions", json=data)
    response_data = response.json()

    if "errors" in response_data:
        error_messages = get_error_messages_from_codes(
            error_codes=set(response_data["errors"][0]["codes"]),
            error_map=TRANSACTION_REGISTRATION_RESULT_ERRORS,
        )
        return PaymentResult(
            status=PaymentStatus.FAILED,
            raw_response=response_data,
            errors=error_messages,
        )

    transaction = response_data["results"][0]
    status = transaction["authori_result"]
    transaction_id = transaction["np_transaction_id"]
    error_messages = []

    if status == PaymentStatus.PENDING:
        if cancel_error_codes := _get_errors(_cancel(config, transaction_id)):
            logger.error(
                "Payment #%s could not be cancelled: %s",
                transaction_id,
                ", ".join(cancel_error_codes),
            )
        error_messages = get_reason_messages_from_codes(
            set(response_data["results"][0]["authori_hold"])
        )

    return PaymentResult(
        status=status,
        psp_reference=transaction_id,
        raw_response=response_data,
        errors=error_messages,
    )


def _cancel(config: ApiConfig, transaction_id: str) -> dict:
    data = {"transactions": [{"np_transaction_id": transaction_id}]}
    response = np_request(config, "patch", "/transactions/cancel", json=data)
    return response.json()


def _get_errors(response_data: dict) -> Iterable[str]:
    if "errors" not in response_data:
        return []
    return set(response_data["errors"][0]["codes"])


def cancel_transaction(
    config: ApiConfig, payment_information: PaymentData
) -> PaymentResult:
    psp_reference = Payment.objects.get(id=payment_information.payment_id).psp_reference

    if not psp_reference:
        raise PaymentError("Payment cannot be voided.")

    status = PaymentStatus.SUCCESS
    response_data = _cancel(config, psp_reference)
    error_messages = []

    if error_codes := _get_errors(response_data):
        status = PaymentStatus.FAILED
        error_messages = get_error_messages_from_codes(
            error_codes, TRANSACTION_CANCELLATION_RESULT_ERROR
        )

    return PaymentResult(
        status=status,
        raw_response=response_data,
        psp_reference=psp_reference,
        errors=error_messages,
    )


def report_fulfillment(config: ApiConfig, fulfillment: Fulfillment):
    # TODO:
    transaction_id = fulfillment.order.payments.latest().psp_reference

    if not transaction_id:
        # TODO: handle errors
        pass

    shipping_company_code = config.shipping_company
    shipping_slip_number = fulfillment.tracking_number

    data = {
        "transactions": [
            {
                "np_transaction_id": transaction_id,
                "pd_company_code": shipping_company_code,
                "slip_no": shipping_slip_number,
            }
        ]
    }
    response = np_request(config, "post", "/shipments", json=data)
    response_data = response.json()

    if error_codes := _get_errors(response_data):
        return get_error_messages_from_codes(
            error_codes, FULFILLMENT_REPORT_RESULT_ERRORS
        )

    return []
