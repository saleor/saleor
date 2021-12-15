import json
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden

from saleor.payment.interface import (
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    PaymentMethodInfo,
)

from . import errors

# Get the logger for this file, it will allow us to log error responses from Tabby.

logger = logging.getLogger(__name__)


def check_payment_supported(payment_information: PaymentData, config: GatewayConfig):
    """Check that a given payment is supported."""
    if payment_information.currency not in config.supported_currencies:
        return errors.UNSUPPORTED_CURRENCY % {"currency": payment_information.currency}


def get_base_api_url():
    base_api_url = "https://api.tabby.ai/api/v1/"

    return base_api_url


def get_default_gateway_response(transaction_kind: str):
    response = GatewayResponse(
        error=None,
        is_success=False,
        raw_response=None,
        transaction_id="",
        amount=Decimal(0),
        action_required=True,
        kind=transaction_kind,
        currency=settings.DEFAULT_CURRENCY,
    )
    return response


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


def _call_tabby_post(data, config, endpoint="/"):
    auth_key = config.connection_params.get("private_key")
    return requests.post(
        url=get_base_api_url() + endpoint,
        headers={
            "Authorization": "Bearer " + auth_key,
            "Content-Type": "application/json",
        },
        json=data,
    ).json()


def _call_tabby_get(data=None, config=None, endpoint="/"):
    auth_key = config.connection_params.get("private_key")
    return requests.get(
        url=get_base_api_url() + endpoint,
        headers={
            "Authorization": "Bearer " + auth_key,
            "Content-Type": "application/json",
        },
        json=data,
    ).json()


def get_exc_message(tabby_response):
    exc_message = ""
    error = tabby_response.get("error")
    if error:
        exc_message = "%s %s" % (
            str(error.capitalize()),
            "please, make sure your app is updated!",
        )
    return exc_message


def verify_webhook(request: HttpRequest, config: GatewayConfig):
    """Verify the request is from Tabby."""

    if request.headers.get(
        config.connection_params.get("webhook_header_title"), ""
    ) != config.connection_params.get("webhook_header_value"):
        return HttpResponseForbidden()
    return True


def handle_webhook(request: HttpRequest, config: GatewayConfig, gateway: str):
    data_from_tabby = json.loads(request.body.decode("utf-8").replace("'", '"'))
    # Verify the webhook signature.
    if verify_webhook(request=request, config=config) is True:
        if data_from_tabby.get("status") == "closed":
            from saleor.payment.models import Payment

            payment_id = data_from_tabby.get("id", {})
            payment = Payment.objects.filter(token=payment_id, gateway=gateway).last()
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
                    logger.info(
                        msg=f"Order #{order.id} created",
                        extra={"order_id": order.id},
                    )
                    return HttpResponse("OK", status=200)
            logger.info(
                msg="Payment is not found",
                extra={"payment_id": data_from_tabby.get("id")},
            )
            return HttpResponse("Payment is not found", status=200)
        logger.info(
            msg="Payment is not closed yet",
            extra={"status": data_from_tabby.get("status")},
        )
        return HttpResponse("Payment is not closed yet!", status=200)
