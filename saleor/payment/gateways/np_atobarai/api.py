import logging
from typing import Dict, List, Optional, Tuple, Union

from ....order.models import Fulfillment, Order
from ...interface import PaymentData
from ...models import Payment
from .api_helpers import (
    cancel,
    format_price,
    get_goods_with_discount,
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
from .const import PRE_FULFILLMENT_ERROR_CODE
from .errors import (
    FULFILLMENT_REPORT,
    NO_PSP_REFERENCE,
    PAYMENT_DOES_NOT_EXIST,
    TRANSACTION_CANCELLATION,
    TRANSACTION_CHANGE,
    TRANSACTION_REGISTRATION,
    add_action_to_code,
    get_error_messages_from_codes,
)
from .utils import get_shipping_company_code, np_atobarai_opentracing_trace

logger = logging.getLogger(__name__)


def register_transaction(
    order: Optional[Order], config: ApiConfig, payment_information: "PaymentData"
) -> PaymentResult:
    """Create a new transaction in NP Atobarai.

    On pending status from NP the transaction is cancelled and
    reason for pending is returned as error message.
    """
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.register"):
        action = TRANSACTION_REGISTRATION
        result, error_codes = register(config, payment_information)

        if error_codes:
            error_messages = get_error_messages_from_codes(
                action, error_codes=error_codes
            )
            return errors_payment_result(error_messages)

        status = result["authori_result"]
        transaction_id = result["np_transaction_id"]
        error_messages = []

        if status == PaymentStatus.PENDING:
            if cancel_error_codes := cancel(config, transaction_id).error_codes:
                handle_unrecoverable_state(
                    order, "cancel", transaction_id, cancel_error_codes
                )
            error_messages = get_error_messages_from_codes(
                action, error_codes=result["authori_hold"]
            )

        return PaymentResult(
            status=status,
            psp_reference=transaction_id,
            errors=error_messages,
        )


def cancel_transaction(
    config: ApiConfig, payment_information: PaymentData
) -> PaymentResult:
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.cancel"):
        action = TRANSACTION_CANCELLATION
        payment_id = payment_information.payment_id
        payment = Payment.objects.filter(id=payment_id).first()

        if not payment:
            return error_payment_result(
                add_action_to_code(action, error_code=PAYMENT_DOES_NOT_EXIST)
            )

        psp_reference = payment.psp_reference

        if not psp_reference:
            return error_payment_result(
                add_action_to_code(action, error_code=NO_PSP_REFERENCE)
            )

        result, error_codes = cancel(config, psp_reference)

        if error_codes:
            error_messages = get_error_messages_from_codes(
                action, error_codes=error_codes
            )
            return errors_payment_result(error_messages)

        return PaymentResult(status=PaymentStatus.SUCCESS)


def change_transaction(
    config: ApiConfig,
    payment: Payment,
    payment_information: PaymentData,
    refund_data: Optional[Dict[int, int]],
) -> Optional[PaymentResult]:
    """Partial refund.

    If the fulfillment was reported prior to changing given transaction,
    then this function is a noop and return value is None.
    """
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.change"):
        if refund_data:
            goods = get_refunded_goods(config, refund_data, payment_information)
        else:
            goods = get_goods_with_discount(config, payment_information)

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
                        payment.order, "cancel", transaction_id, cancel_error_codes
                    )
                error_messages = result["authori_hold"]
                return errors_payment_result(error_messages)

            return PaymentResult(
                status=PaymentStatus.SUCCESS,
            )

        if PRE_FULFILLMENT_ERROR_CODE in error_codes:
            logger.info(
                "Fulfillment for payment with id %s was reported",
                payment_information.graphql_payment_id,
            )
            return None

        error_messages = get_error_messages_from_codes(
            action=TRANSACTION_CHANGE, error_codes=error_codes
        )
        return errors_payment_result(error_messages)


def reregister_transaction_for_partial_return(
    config: ApiConfig,
    payment: Payment,
    payment_information: PaymentData,
    shipping_company_code: Optional[str],
    tracking_number: Optional[str],
    refund_data: Optional[Dict[int, int]],
) -> PaymentResult:
    """Partial refund after fulfillment report."""
    with np_atobarai_opentracing_trace("np-atobarai.checkout.payments.reregister"):
        psp_reference = payment.psp_reference
        action = TRANSACTION_REGISTRATION

        if not psp_reference:
            return error_payment_result(
                add_action_to_code(
                    action,
                    error_code=NO_PSP_REFERENCE,
                )
            )

        if cancel_error_codes := cancel(config, psp_reference).error_codes:
            error_messages = get_error_messages_from_codes(
                action=TRANSACTION_CANCELLATION, error_codes=cancel_error_codes
            )
            return errors_payment_result(error_messages)

        if refund_data:
            goods = get_refunded_goods(config, refund_data, payment_information)
        else:
            goods = get_goods_with_discount(config, payment_information)

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

            report(config, shipping_company_code, new_psp_reference, tracking_number)

            return PaymentResult(
                status=PaymentStatus.SUCCESS,
                psp_reference=new_psp_reference,
            )

        error_messages = get_error_messages_from_codes(action, error_codes=error_codes)

        return errors_payment_result(error_messages)


def report_fulfillment(
    config: ApiConfig, payment: Payment, fulfillment: Fulfillment
) -> Tuple[Union[str, int], List[str], bool]:
    with np_atobarai_opentracing_trace(
        "np-atobarai.checkout.payments.report-fulfillment"
    ):
        payment_id = payment.psp_reference or payment.id
        already_reported = False
        shipping_company_code = get_shipping_company_code(config, fulfillment)

        result, error_codes = report(
            config,
            shipping_company_code,
            payment.psp_reference,
            fulfillment.tracking_number,
        )

        if PRE_FULFILLMENT_ERROR_CODE in error_codes:
            already_reported = True

        errors = get_error_messages_from_codes(
            action=FULFILLMENT_REPORT, error_codes=error_codes
        )

        return payment_id, errors, already_reported
