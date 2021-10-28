import logging
from typing import List, Optional, Tuple, Union

from ....order.models import Fulfillment
from ...interface import PaymentData, RefundLineData
from ...models import Payment
from .api_helpers import (
    cancel,
    format_price,
    get_discount,
    get_refunded_goods,
    handle_unrecoverable_state,
    np_request,
    register,
    report,
)
from .api_types import (
    ApiConfig,
    PaymentResult,
    PaymentStatus,
    error_payment_result,
    errors_payment_result,
)
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
        result, error_codes = register(config, payment_information)

        if error_codes:
            error_messages = get_error_messages_from_codes(
                error_codes=error_codes,
                error_map=TRANSACTION_REGISTRATION_RESULT_ERRORS,
            )
            return errors_payment_result(error_messages)

        status = result["authori_result"]
        transaction_id = result["np_transaction_id"]
        error_messages = []

        if status == PaymentStatus.PENDING:
            if cancel_error_codes := cancel(config, transaction_id).error_codes:
                handle_unrecoverable_state("cancel", transaction_id, cancel_error_codes)
            error_messages = get_reason_messages_from_codes(result["authori_hold"])

        return PaymentResult(
            status=status,
            psp_reference=transaction_id,
            errors=error_messages,
        )


def cancel_transaction(
    config: ApiConfig, payment_information: PaymentData
) -> PaymentResult:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.cancel"):
        payment_id = payment_information.payment_id
        payment = Payment.objects.filter(id=payment_id).first()

        if not payment:
            return error_payment_result(f"Payment with id {payment_id} does not exist.")

        psp_reference = payment.psp_reference

        if not psp_reference:
            return error_payment_result(
                f"Payment with id {payment_id} cannot be voided "
                f"- psp reference is missing."
            )

        result, error_codes = cancel(config, psp_reference)

        if error_codes:
            error_messages = get_error_messages_from_codes(
                error_codes, TRANSACTION_CANCELLATION_RESULT_ERROR
            )
            return errors_payment_result(error_messages)

        return PaymentResult(status=PaymentStatus.SUCCESS)


PRE_FULFILLMENT_ERROR_CODE = "E0100115"


def change_transaction(
    config: ApiConfig,
    payment: Payment,
    payment_information: PaymentData,
    lines: Optional[List[RefundLineData]],
) -> Optional[PaymentResult]:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.change"):
        if lines:
            goods = get_refunded_goods(lines, payment_information)
        else:
            goods = get_discount(payment_information)

        data = {
            "transactions": [
                {
                    "np_transaction_id": payment.psp_reference,
                    "billed_amount": format_price(
                        payment.captured_amount - payment_information.amount,
                        payment_information.currency,
                    ),
                    "goods": goods,
                }
            ]
        }

        result, error_codes = np_request(
            config, "patch", "/transactions/update", json=data
        )

        if not error_codes:
            status = result["authori_result"]
            transaction_id = result["np_transaction_id"]

            if status == PaymentStatus.PENDING:
                if cancel_error_codes := cancel(config, transaction_id).error_codes:
                    handle_unrecoverable_state(
                        "cancel", transaction_id, cancel_error_codes
                    )
                error_messages = get_reason_messages_from_codes(result["authori_hold"])
                return errors_payment_result(error_messages)

            return PaymentResult(
                status=PaymentStatus.SUCCESS,
            )

        if PRE_FULFILLMENT_ERROR_CODE in error_codes:
            return None

        error_messages = get_error_messages_from_codes(
            error_codes, TRANSACTION_REGISTRATION_RESULT_ERRORS
        )
        return errors_payment_result(error_messages)


# TODO: find code
ALREADY_REREGISTERED_ERROR_CODE = "E0131006"
EXCEEDED_NUMBER_OF_REREGISTRATIONS_ERROR_CODE = "E0131011"


def reregister_transaction_for_partial_return(
    config: ApiConfig,
    payment: Payment,
    payment_information: PaymentData,
    tracking_number: Optional[str],
    lines: Optional[List[RefundLineData]],
) -> PaymentResult:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.reregister"):
        payment_id = payment_information.payment_id
        psp_reference = payment.psp_reference

        if not psp_reference:
            return error_payment_result(
                f"Payment with id {payment_id} cannot be reregistered "
                f"- psp reference is missing."
            )

        if cancel_error_codes := cancel(config, psp_reference).error_codes:
            error_messages = get_error_messages_from_codes(
                cancel_error_codes, TRANSACTION_CANCELLATION_RESULT_ERROR
            )
            return errors_payment_result(error_messages)

        if lines:
            goods = get_refunded_goods(lines, payment_information)
        else:
            goods = get_discount(payment_information)

        billed_amount = format_price(
            payment.captured_amount - payment_information.amount,
            payment_information.currency,
        )

        result, error_codes = register(
            config,
            payment_information,
            billed_amount,
            goods,
        )

        if not error_codes:
            new_psp_reference = result["np_transaction_id"]

            report(config, new_psp_reference, tracking_number)

            return PaymentResult(
                status=PaymentStatus.SUCCESS,
                psp_reference=new_psp_reference,
            )

        error_messages = get_error_messages_from_codes(
            error_codes, TRANSACTION_REGISTRATION_RESULT_ERRORS
        )

        if register_error_codes := register(config, payment_information).error_codes:
            handle_unrecoverable_state("uncancel", psp_reference, register_error_codes)

        return errors_payment_result(error_messages)


def report_fulfillment(
    config: ApiConfig, payment: Payment, fulfillment: Fulfillment
) -> Tuple[Union[str, int], List[str], bool]:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.capture"):
        payment_id = payment.psp_reference or payment.id
        already_reported = False

        result, error_codes = report(
            config, payment.psp_reference, fulfillment.tracking_number
        )

        if PRE_FULFILLMENT_ERROR_CODE in error_codes:
            already_reported = True

        errors = get_error_messages_from_codes(
            error_codes, FULFILLMENT_REPORT_RESULT_ERRORS
        )

        return payment_id, errors, already_reported
