from decimal import Decimal

from checkout_sdk.errors import CheckoutSdkError
from django.utils.translation import gettext_lazy as _

from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData
from .utils import (
    _error_response,
    _success_response,
    check_payment_supported,
    generate_checkout_request_data_frames,
    get_amount_for_checkout,
    get_checkout_client,
    get_error_message_from_checkout_error,
    get_payment_customer_id,
)


def process_payment_using_frames(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process a payment using the Checkout client."""
    response = GatewayResponse(
        error=None,
        is_success=False,
        raw_response=None,
        transaction_id="",
        action_required=True,
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
    )

    error = check_payment_supported(
        payment_information=payment_information, config=config
    )

    if not error:
        try:
            checkout_amount = get_amount_for_checkout(amount=payment_information.amount)
            request_data = generate_checkout_request_data_frames(
                amount=checkout_amount,
                payment_information=payment_information,
            )
            checkout_client = get_checkout_client(**config.connection_params)
            payment = checkout_client.payments.request(**request_data)
        except CheckoutSdkError as exc:
            error = get_error_message_from_checkout_error(exc)
            response = _error_response(
                exc=error,
                action_required=True,
                kind=TransactionKind.AUTH,
                payment_info=payment_information,
                raw_response={
                    "error_type": exc.error_type,
                    "request_id": exc.request_id,
                    "http_status": exc.http_status,
                    "error_codes": exc.error_codes,
                },
            )
        else:
            response = _success_response(
                token=payment.id,
                action_required=True,
                kind=TransactionKind.AUTH,
                amount=payment_information.amount,
                currency=payment_information.currency,
                payment_response=payment.http_response.body,
                customer_id=get_payment_customer_id(payment_information),
                action_required_data={"3ds_url": payment.redirect_link.get("href")},
            )
            from saleor.payment.models import Payment

            payment_instance = Payment.objects.get(pk=payment_information.payment_id)
            payment_instance.token = payment.id
            payment_instance.psp_reference = payment.http_response.body.get("reference")
            payment_instance.save(update_fields=["token", "psp_reference"])
    return response


def capture_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Capture an authorized payment using the Checkout client.

    But it is first check if the given payment instance is supported
    by the gateway.
    If an error from Checkout occurs, we flag the transaction as failed and return
    a short user-friendly description of the error after logging the error to stderr.
    """
    try:
        checkout_client = get_checkout_client(**config.connection_params)
        from saleor.payment.models import Payment

        payment_id = Payment.objects.get(pk=payment_information.payment_id).token
        checkout_amount = get_amount_for_checkout(amount=payment_information.amount)
        payment = checkout_client.payments.capture(
            payment_id=payment_id, amount=checkout_amount, reference="CAPTURE"
        )
    except CheckoutSdkError as exc:
        error = get_error_message_from_checkout_error(exc)
        response = _error_response(
            exc=error,
            action_required=True,
            kind=TransactionKind.CAPTURE,
            payment_info=payment_information,
            raw_response={
                "request_id": exc.request_id,
                "error_type": exc.error_type,
                "http_status": exc.http_status,
                "error_codes": exc.error_codes,
            },
        )
    else:
        if payment.http_response.status == 202 and payment.http_response.body.get(
            "action_id"
        ):
            response = _success_response(
                action_required=True,
                kind=TransactionKind.AUTH,
                token=payment_information.token,
                amount=payment_information.amount,
                currency=payment_information.currency,
                payment_response=payment.http_response.body,
                customer_id=get_payment_customer_id(payment_information),
            )
        else:
            response = _error_response(
                action_required=True,
                kind=TransactionKind.CAPTURE,
                payment_info=payment_information,
                raw_response=payment.http_response.body,
                exc=_("Payment capture transaction was unsuccessful"),
            )
    return response


def refund_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Refund a payment using the checkout client.

    But it is first check if the given payment instance is supported
    by the gateway.
    It first retrieves a `charge` transaction to retrieve the
    payment id to refund. And return an error with a failed transaction
    if the there is no such transaction, or if an error
    from Checkout occurs during the refund.
    """
    try:
        checkout_client = get_checkout_client(**config.connection_params)
        from saleor.payment.models import Payment

        payment_id = Payment.objects.get(pk=payment_information.payment_id).token
        checkout_amount = get_amount_for_checkout(amount=payment_information.amount)
        payment = checkout_client.payments.refund(
            payment_id=payment_id, amount=checkout_amount, reference="REFUND"
        )
    except CheckoutSdkError as exc:
        error = get_error_message_from_checkout_error(exc)
        response = _error_response(
            exc=error,
            action_required=True,
            kind=TransactionKind.REFUND,
            payment_info=payment_information,
            raw_response={
                "request_id": exc.request_id,
                "http_status": exc.http_status,
                "error_type": exc.error_type,
                "error_codes": exc.error_codes,
            },
        )
    else:
        if payment.http_response.status == 202 and payment.http_response.body.get(
            "action_id"
        ):
            response = _success_response(
                action_required=False,
                kind=TransactionKind.REFUND,
                token=payment_information.token,
                amount=payment_information.amount,
                currency=payment_information.currency,
                payment_response=payment.http_response.body,
                customer_id=get_payment_customer_id(payment_information),
            )
        else:
            response = _error_response(
                action_required=True,
                kind=TransactionKind.REFUND,
                payment_info=payment_information,
                raw_response=payment.http_response.body,
                exc=_("Payment refund transaction was unsuccessful"),
            )
    return response


def confirm(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    try:
        checkout_client = get_checkout_client(**config.connection_params)

        from saleor.payment.models import Payment

        payment_id = Payment.objects.get(pk=payment_information.payment_id).token
        payment = checkout_client.payments.get(payment_id=payment_id)
    except CheckoutSdkError as exc:
        error = get_error_message_from_checkout_error(exc)
        response = _error_response(
            exc=error,
            action_required=True,
            kind=TransactionKind.CAPTURE,
            payment_info=payment_information,
            raw_response={
                "error_type": exc.error_type,
                "request_id": exc.request_id,
                "http_status": exc.http_status,
                "error_codes": exc.error_codes,
            },
        )
    else:
        checkout_amount = get_amount_for_checkout(payment_information.amount)
        if (
            payment.http_response.status == 200
            and payment.http_response.body.get("approved") is True
            and Decimal(payment.http_response.body.get("amount")) == checkout_amount
            and payment.http_response.body.get("status") in ["Authorized", "Captured"]
            and payment.http_response.body.get("currency")
            == payment_information.currency
        ):
            response = _success_response(
                action_required=False,
                kind=TransactionKind.CAPTURE,
                token=payment_information.token,
                amount=payment_information.amount,
                currency=payment_information.currency,
                payment_response=payment.http_response.body,
                customer_id=get_payment_customer_id(payment_information),
            )
        else:
            response = _error_response(
                action_required=True,
                kind=TransactionKind.CAPTURE,
                payment_info=payment_information,
                raw_response=payment.http_response.body,
                exc=str(_("Payment transaction was unsuccessful")),
            )
    return response


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    return process_payment_using_frames(
        payment_information=payment_information, config=config
    )


def confirm_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    return confirm(payment_information=payment_information, config=config)


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    return capture_payment(payment_information=payment_information, config=config)


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    return refund_payment(payment_information=payment_information, config=config)
