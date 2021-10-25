import logging
from typing import List, Optional, Tuple, Union

from django.utils import timezone

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
)
from .api_types import ApiConfig, PaymentResult, PaymentStatus, error_payment_result
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
            return PaymentResult(
                status=PaymentStatus.FAILED,
                errors=error_messages,
            )

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

        status = PaymentStatus.SUCCESS
        result, error_codes = cancel(config, psp_reference)
        error_messages = []

        if error_codes:
            status = PaymentStatus.FAILED
            error_messages = get_error_messages_from_codes(
                error_codes, TRANSACTION_CANCELLATION_RESULT_ERROR
            )

        return PaymentResult(
            status=status,
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
                return PaymentResult(
                    status=PaymentStatus.FAILED,
                    errors=error_messages,
                )

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
            return error_payment_result(
                f"Payment with id {payment_id} cannot be reregistered "
                f"- psp reference is missing."
            )

        if cancel_error_codes := cancel(config, psp_reference).error_codes:
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
            goods = get_refunded_goods(lines, payment_information)
        else:
            goods = get_discount(payment_information)

        data = {
            "transactions": [
                {
                    "base_np_transaction_id": psp_reference,
                    "shop_transaction_id": payment_id,
                    "shop_order_date": order_date,
                    "billed_amount": format_price(
                        payment.captured_amount - payment_information.amount,
                        payment_information.currency,
                    ),
                    "goods": goods,
                }
            ]
        }

        result, error_codes = np_request(
            config, "post", "/transactions/reregister", json=data
        )

        if not error_codes:
            new_psp_reference = result["np_transaction_id"]

            return PaymentResult(
                status=PaymentStatus.SUCCESS,
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

        if register_error_codes := register(config, payment_information).error_codes:
            handle_unrecoverable_state("uncancel", psp_reference, register_error_codes)

        return PaymentResult(
            status=PaymentStatus.FAILED,
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

        result, error_codes = np_request(config, "post", "/shipments", json=data)

        # check if the payment was already captured
        if PRE_FULFILLMENT_ERROR_CODE in error_codes:
            return psp_reference, [], True

        errors = get_error_messages_from_codes(
            error_codes, FULFILLMENT_REPORT_RESULT_ERRORS
        )

        return psp_reference, errors, False
