import logging
from typing import Iterable, List, Optional

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
from .utils import np_atobarai_opentracing_trace

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
    with np_atobarai_opentracing_trace("np-atobarai.utilities.request"):
        response = requests.request(
            method=method,
            url=get_url(config, path),
            timeout=REQUEST_TIMEOUT,
            json=json or {},
            auth=HTTPBasicAuth(config.merchant_code, config.sp_code),
            headers={"X-NP-Terminal-Id": config.terminal_id},
        )
        if 400 < response.status_code <= 600:
            raise requests.HTTPError
        return response


def np_request(
    config: ApiConfig, method: str, path: str = "", json: Optional[dict] = None
) -> requests.Response:
    try:
        return _request(config, method, path, json)
    except requests.RequestException:
        msg = "Cannot connect to NP Atobarai."
        logger.warning(msg, exc_info=True)
        raise PaymentError(msg)


def _get_errors(response_data: dict) -> Iterable[str]:
    if "errors" not in response_data:
        return []
    return set(response_data["errors"][0]["codes"])


def health_check(config: ApiConfig) -> bool:
    try:
        _request(config, "post", "/authorizations/find")
        return True
    except requests.RequestException:
        return False


def _format_name(ad: AddressData):
    """Follow the Japanese name guidelines."""
    return f"{ad.first_name} {ad.last_name}".strip()


def _format_address(config: ApiConfig, ad: AddressData):
    """Follow the Japanese address guidelines."""
    # example: "東京都千代田区麹町４－２－６　住友不動産麹町ファーストビル５階"
    if not config.fill_missing_address:
        return f"{ad.country_area}{ad.street_address_2}{ad.street_address_1}"
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
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.register"):
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


def change_transaction(
    config: ApiConfig,
    payment: Payment,
    payment_information: PaymentData,
) -> PaymentResult:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.change"):
        data = {
            "transactions": [
                {
                    "np_transaction_id": payment.psp_reference,
                    "billed_amount": int(
                        price_to_minor_unit(
                            payment.captured_amount - payment_information.amount,
                            payment_information.currency,
                        )
                    ),
                }
            ]
        }

        response = np_request(config, "patch", "/transactions/update", json=data)
        response_data = response.json()

        status = PaymentStatus.SUCCESS
        error_messages = []

        if error_codes := _get_errors(response_data):
            status = PaymentStatus.FAILED
            error_messages = get_error_messages_from_codes(
                error_codes, TRANSACTION_REGISTRATION_RESULT_ERRORS
            )

        return PaymentResult(
            status=status,
            psp_reference=payment.psp_reference or "",
            errors=error_messages,
        )


def _cancel(config: ApiConfig, transaction_id: str) -> dict:
    data = {"transactions": [{"np_transaction_id": transaction_id}]}
    response = np_request(config, "patch", "/transactions/cancel", json=data)
    return response.json()


def cancel_transaction(
    config: ApiConfig, payment_information: PaymentData
) -> PaymentResult:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.cancel"):
        payment_id = payment_information.payment_id
        payment = Payment.objects.filter(id=payment_id).first()

        if not payment:
            raise PaymentError(f"Payment with id {payment_id} does not exist.")

        psp_reference = payment.psp_reference

        if not psp_reference:
            raise PaymentError(
                f"Payment with id {payment_id} cannot be voided "
                f"- psp reference is missing."
            )

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


def report_fulfillment(config: ApiConfig, fulfillment: Fulfillment) -> List[str]:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.capture"):
        payment = fulfillment.order.get_last_payment()

        if not payment:
            return ["Payment does not exist for this order."]

        transaction_id = payment.psp_reference

        if not transaction_id:
            return ["Payment does not have psp reference."]

        shipping_company_code = config.shipping_company
        shipping_slip_number = fulfillment.tracking_number

        if not shipping_slip_number:
            return ["Fulfillment does not have tracking number."]

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

        return get_error_messages_from_codes(
            _get_errors(response_data), FULFILLMENT_REPORT_RESULT_ERRORS
        )
