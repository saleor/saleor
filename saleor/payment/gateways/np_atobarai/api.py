import logging
from typing import List, Optional, Tuple, Union

from django.utils import timezone

from ....order.models import Fulfillment
from ... import PaymentError
from ...interface import PaymentData, RefundLineData
from ...models import Payment
from .api_helpers import (
    _cancel,
    _format_price,
    _get_discount,
    _get_errors,
    _get_refunded_goods,
    _handle_unrecoverable_state,
    _register,
    np_request,
)
from .api_types import ApiConfig, PaymentResult, PaymentStatus
from .errors import (
    FULFILLMENT_REPORT_RESULT_ERRORS,
    TRANSACTION_CANCELLATION_RESULT_ERROR,
    TRANSACTION_REGISTRATION_RESULT_ERRORS,
    get_error_messages_from_codes,
    get_reason_messages_from_codes,
)
from .utils import np_atobarai_opentracing_trace

logger = logging.getLogger(__name__)


def register_transaction(
    config: ApiConfig, payment_information: "PaymentData"
) -> PaymentResult:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.register"):
        response_data = _register(config, payment_information)

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
                _handle_unrecoverable_state(
                    "cancel", transaction_id, cancel_error_codes
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


PRE_FULFILLMENT_ERROR_CODE = "E0100115"


def change_transaction(
    config: ApiConfig,
    payment: Payment,
    payment_information: PaymentData,
    lines: Optional[List[RefundLineData]],
) -> Optional[PaymentResult]:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.change"):
        if lines:
            goods = _get_refunded_goods(lines, payment_information)
        else:
            goods = _get_discount(payment_information)

        data = {
            "transactions": [
                {
                    "np_transaction_id": payment.psp_reference,
                    "billed_amount": _format_price(
                        payment.captured_amount - payment_information.amount,
                        payment_information.currency,
                    ),
                    "goods": goods,
                }
            ]
        }

        response = np_request(config, "patch", "/transactions/update", json=data)
        response_data = response.json()

        error_codes = _get_errors(response_data)

        if not error_codes:
            return PaymentResult(
                status=PaymentStatus.SUCCESS,
            )

        if PRE_FULFILLMENT_ERROR_CODE in error_codes:
            return None

        error_messages = get_error_messages_from_codes(
            error_codes, TRANSACTION_REGISTRATION_RESULT_ERRORS
        )
        return PaymentResult(status=PaymentStatus.FAILED, errors=error_messages)


# TODO: find code
ALREADY_REREGISTERED_ERROR_CODE = "E0131006"
EXCEEDED_NUMBER_OF_REREGISTRATIONS_ERROR_CODE = "E0131011"


def reregister_transaction_for_partial_return(
    config: ApiConfig,
    payment: Payment,
    payment_information: PaymentData,
    lines: Optional[List[RefundLineData]],
) -> PaymentResult:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.reregister"):
        payment_id = payment_information.payment_id
        psp_reference = payment.psp_reference

        if not psp_reference:
            raise PaymentError(
                f"Payment with id {payment_id} cannot be reregistered "
                f"- psp reference is missing."
            )

        if cancel_error_codes := _get_errors(_cancel(config, psp_reference)):
            return PaymentResult(
                status=PaymentStatus.FAILED,
                errors=(
                    get_error_messages_from_codes(
                        cancel_error_codes, TRANSACTION_CANCELLATION_RESULT_ERROR
                    )
                ),
            )

        # TODO: probably use order date from registration?????
        order_date = timezone.now().strftime("%Y-%m-%d")

        if lines:
            goods = _get_refunded_goods(lines, payment_information)
        else:
            goods = _get_discount(payment_information)

        data = {
            "transactions": [
                {
                    "base_np_transaction_id": psp_reference,
                    "shop_transaction_id": payment_id,
                    "shop_order_date": order_date,
                    "billed_amount": _format_price(
                        payment.captured_amount - payment_information.amount,
                        payment_information.currency,
                    ),
                    "goods": goods,
                }
            ]
        }

        response = np_request(config, "post", "/transactions/reregister", json=data)
        response_data = response.json()

        error_codes = _get_errors(response_data)

        if not error_codes:
            new_psp_reference = response_data["results"][0]["np_transaction_id"]

            return PaymentResult(
                status=PaymentStatus.SUCCESS,
                raw_response=response_data,
                psp_reference=new_psp_reference,
            )

        if ALREADY_REREGISTERED_ERROR_CODE in error_codes:
            return PaymentResult(
                status=PaymentStatus.FAILED,
                errors=["NP Transaction was already re-registered."],
            )

        if EXCEEDED_NUMBER_OF_REREGISTRATIONS_ERROR_CODE in error_codes:
            return PaymentResult(
                status=PaymentStatus.FAILED,
                errors=["Number of NP Transaction re-registrations was exceeded."],
            )

        error_messages = get_error_messages_from_codes(
            error_codes, TRANSACTION_REGISTRATION_RESULT_ERRORS
        )

        if register_error_codes := _get_errors(_register(config, payment_information)):
            _handle_unrecoverable_state("uncancel", psp_reference, register_error_codes)

        return PaymentResult(
            status=PaymentStatus.FAILED,
            raw_response=response_data,
            errors=error_messages,
        )


def report_fulfillment(
    config: ApiConfig, payment: Payment, fulfillment: Fulfillment
) -> Tuple[Union[str, int], List[str], bool]:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.capture"):

        psp_reference = payment.psp_reference

        if not psp_reference:
            return payment.id, ["Payment does not have psp reference."], False

        shipping_company_code = config.shipping_company
        shipping_slip_number = fulfillment.tracking_number

        if not shipping_slip_number:
            return psp_reference, ["Fulfillment does not have tracking number."], False

        data = {
            "transactions": [
                {
                    "np_transaction_id": psp_reference,
                    "pd_company_code": shipping_company_code,
                    "slip_no": shipping_slip_number,
                }
            ]
        }
        try:
            response = np_request(config, "post", "/shipments", json=data)
        except PaymentError as pe:
            return psp_reference, [pe.message], False

        response_data = response.json()

        error_codes = _get_errors(response_data)

        # check if the payment was already captured
        if PRE_FULFILLMENT_ERROR_CODE in error_codes:
            return psp_reference, [], True

        errors = get_error_messages_from_codes(
            _get_errors(response_data), FULFILLMENT_REPORT_RESULT_ERRORS
        )

        return psp_reference, errors, False
