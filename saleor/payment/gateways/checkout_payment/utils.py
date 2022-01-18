import hashlib
import hmac
import json
import logging
from decimal import Decimal

import checkout_sdk as checkout
import checkout_sdk.errors as checkout_errors
import graphene
import requests
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden

from saleor.payment import ChargeStatus
from saleor.payment.interface import (
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    PaymentMethodInfo,
)

from . import errors

# Get the logger for this file, it will allow us to log error responses from checkout.
logger = logging.getLogger(__name__)


def get_checkout_client(private_key: str, sandbox: bool, **_):
    """Create a Checkout client from set-up application keys."""
    checkout_client = checkout.get_api(secret_key=private_key, sandbox=sandbox)
    return checkout_client


def get_amount_for_checkout(amount: Decimal) -> int:
    """Convert an amount to checkout amount (needed by Checkout).

    Multiplies the value by 100.
    """
    return int(amount * 100)


def check_payment_supported(payment_information: PaymentData, config: GatewayConfig):
    """Check that a given payment is supported."""
    if payment_information.currency not in config.supported_currencies.split(","):
        return errors.UNSUPPORTED_CURRENCY % {"currency": payment_information.currency}


def get_error_message_from_checkout_error(exc: BaseException):
    """Convert a Checkout error to a user-friendly error message.

    It also logs the exception to stderr.
    """
    if isinstance(exc, checkout_errors.ValidationError):
        return errors.INVALID_REQUEST
    else:
        return errors.SERVER_ERROR


def _success_response(
    kind: str,
    payment_response: dict,
    token=None,
    amount=None,
    currency=None,
    customer_id=None,
    raw_response=None,
    action_required=True,
    action_required_data: dict = None,
):
    return GatewayResponse(
        kind=kind,
        error=None,
        amount=amount,
        is_success=True,
        currency=currency,
        transaction_id=token,
        customer_id=customer_id,
        action_required=action_required,
        action_required_data=action_required_data,
        raw_response=raw_response or payment_response,
        payment_method_info=PaymentMethodInfo(type="card"),
    )


def _error_response(
    exc,
    kind: str,
    payment_info: PaymentData,
    raw_response: dict = None,
    action_required: bool = False,
) -> GatewayResponse:
    return GatewayResponse(
        error=exc,
        kind=kind,
        is_success=False,
        raw_response=raw_response,
        amount=payment_info.amount,
        currency=payment_info.currency,
        action_required=action_required,
        customer_id=payment_info.customer_id,
        transaction_id=str(payment_info.token),
        payment_method_info=PaymentMethodInfo(type="card"),
    )


def generate_checkout_request_data_frames(amount, payment_information):
    from saleor.account.models import User
    from saleor.payment.models import Payment

    card_type = Payment.objects.get(
        pk=payment_information.payment_id, is_active=True
    ).get_value_from_metadata("card_type")

    request_data = {
        "source": {"type": "token", "token": payment_information.token},
        "customer": {
            "email": payment_information.customer_email,
            "name": User.objects.get(
                email=payment_information.customer_email
            ).get_full_name(),
        },
        "3ds": {
            "enabled": True,
            "attempt_n3d": True,
        },
        "amount": amount,
        "reference": payment_information.token,
        "currency": payment_information.currency,
    }
    if card_type == "mada":
        request_data.update({"metadata": {"udf1": "mada"}})
    return request_data


def get_payment_customer_id(payment_information):
    from saleor.account.models import User

    pk = User.objects.filter(email=payment_information.customer_email).first().id
    return graphene.Node.to_global_id("User", pk) if pk else ""


def verify_webhook(request: HttpRequest, secret_key):
    h = hmac.new(
        msg=request.body,
        digestmod=hashlib.sha256,
        key=secret_key.encode("utf-8"),
    ).hexdigest()
    if h != request.headers.get("Cko-Signature", ""):
        return HttpResponseForbidden()
    return True


def handle_webhook(request: HttpRequest, config: GatewayConfig, gateway: str):
    secret_key = config.connection_params.get("private_key", None)
    data_from_checkout = json.loads(request.body.decode("utf-8").replace("'", '"'))
    # Verify the webhook signature.
    if verify_webhook(request=request, secret_key=secret_key) is True:
        if data_from_checkout.get("type") == "payment_captured":
            payment_data = data_from_checkout.get("data", {})
            if payment_data:
                payment_id = payment_data.get("id", None)
                from saleor.payment.models import Payment

                payment = Payment.objects.filter(
                    token=payment_id, gateway=gateway
                ).last()
                if payment is not None:
                    if payment.checkout:
                        # Create the order into the database
                        from saleor.payment.gateways.adyen.webhooks import create_order
                        from saleor.plugins.manager import get_plugins_manager

                        order = create_order(
                            payment=payment,
                            checkout=payment.checkout,
                            manager=get_plugins_manager(),
                        )

                        # Mark the payment as paid
                        amount = Decimal(payment_data.get("amount")) / 100
                        payment.captured_amount = amount
                        payment.charge_status = (
                            ChargeStatus.FULLY_CHARGED
                            if amount >= payment.total
                            else ChargeStatus.PARTIALLY_CHARGED
                        )
                        payment.save(
                            update_fields=[
                                "modified",
                                "charge_status",
                                "captured_amount",
                            ]
                        )

                        # Remove the unneeded payments from the database.
                        for p in payment.checkout.payments.exclude(id=payment.id):
                            p.transactions.all().delete()
                            p.delete()

                        logger.info(
                            msg=f"Order #{order.id} created",
                            extra={"order_id": order.id},
                        )
                        return HttpResponse("OK", status=200)
                return HttpResponse("Payment not found", status=200)


def validate_apple_pay_session(request: HttpRequest) -> HttpResponse:
    url = json.loads(request.body.decode("utf-8").replace("'", '"'))

    if url:
        requests.post(url=url, headers={"Content-Type": "application/json"})
        return HttpResponse(url)
    raise Http404()
