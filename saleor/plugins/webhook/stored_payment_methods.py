import logging
from typing import Optional, cast

import graphene
from django.core.cache import cache

from ...app.models import App
from ...payment import TokenizedPaymentFlow
from ...payment.interface import (
    PaymentGateway,
    PaymentGatewayInitializeTokenizationResponseData,
    PaymentGatewayInitializeTokenizationResult,
    PaymentMethodCreditCardInfo,
    PaymentMethodData,
    PaymentMethodTokenizationResponseData,
    PaymentMethodTokenizationResult,
    StoredPaymentMethodRequestDeleteResponseData,
    StoredPaymentMethodRequestDeleteResult,
)
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.utils import get_webhooks_for_event
from .utils import generate_cache_key_for_webhook, to_payment_app_id

logger = logging.getLogger(__name__)


def get_credit_card_info(
    app: App, credit_card_info: dict
) -> Optional[PaymentMethodCreditCardInfo]:
    required_fields = [
        "brand",
        "lastDigits",
        "expYear",
        "expMonth",
    ]
    brand = credit_card_info.get("brand")
    last_digits = credit_card_info.get("lastDigits")
    exp_year = credit_card_info.get("expYear")
    exp_month = credit_card_info.get("expMonth")
    first_digits = credit_card_info.get("firstDigits")
    if not all(field in credit_card_info for field in required_fields):
        logger.warning(
            "Skipping stored payment method. Missing required fields for credit card "
            "info. Required fields: %s, received fields: %s from app %s.",
            required_fields,
            credit_card_info.keys(),
            app.id,
        )
        return None
    if not all([brand, last_digits, exp_year, exp_month]):
        logger.warning("Skipping stored credit card info without required fields")
        return None
    if not isinstance(exp_year, int):
        if isinstance(exp_year, str) and exp_year.isdigit():
            exp_year = int(exp_year)
        else:
            logger.warning(
                "Skipping stored payment method with invalid expYear, "
                "received from app %s",
                app.id,
            )
            return None

    if not isinstance(exp_month, int):
        if isinstance(exp_month, str) and exp_month.isdigit():
            exp_month = int(exp_month)
        else:
            logger.warning(
                "Skipping stored payment method with invalid expMonth, "
                "received from app %s",
                app.id,
            )
            return None

    return PaymentMethodCreditCardInfo(
        brand=str(brand),
        last_digits=str(last_digits),
        exp_year=exp_year,
        exp_month=exp_month,
        first_digits=str(first_digits) if first_digits else None,
    )


def get_payment_method_from_response(
    app: "App", payment_method: dict, currency: str
) -> Optional[PaymentMethodData]:
    payment_method_external_id = payment_method.get("id")
    if not payment_method_external_id:
        logger.warning(
            "Skipping stored payment method without id, received from app %s", app.id
        )
        return None
    payment_method_type = payment_method.get("type")
    if not payment_method_type:
        logger.warning(
            "Skipping stored payment method without type, received from app %s",
            app.id,
        )
        return None

    supported_payment_flows = payment_method.get("supportedPaymentFlows")
    if not supported_payment_flows or not isinstance(supported_payment_flows, list):
        logger.warning(
            "Skipping stored payment method with incorrect `supportedPaymentFlows`, "
            "received from app %s",
            app.id,
        )
        return None
    payment_flow_choices = {
        flow[0].upper(): flow[0] for flow in TokenizedPaymentFlow.CHOICES
    }
    if set(supported_payment_flows).difference(payment_flow_choices.keys()):
        logger.warning(
            "Skipping stored payment method with unsupported payment flows, "
            "received from app %s",
            app.id,
        )
        return None
    app_identifier = cast(str, app.identifier)
    credit_card_info = payment_method.get("creditCardInfo")
    name = payment_method.get("name")
    return PaymentMethodData(
        id=to_payment_app_id(app, payment_method_external_id),
        external_id=payment_method_external_id,
        supported_payment_flows=[
            payment_flow_choices[flow] for flow in supported_payment_flows
        ],
        type=payment_method_type,
        credit_card_info=get_credit_card_info(app, credit_card_info)
        if credit_card_info
        else None,
        name=name if name else None,
        data=payment_method.get("data"),
        gateway=PaymentGateway(
            id=app_identifier, name=app.name, currencies=[currency], config=[]
        ),
    )


def get_list_stored_payment_methods_from_response(
    app: "App", response_data: dict, currency: str
) -> list["PaymentMethodData"]:
    payment_methods_response = response_data.get("paymentMethods", [])
    payment_methods = []
    for payment_method in payment_methods_response:
        if parsed_payment_method := get_payment_method_from_response(
            app, payment_method, currency
        ):
            payment_methods.append(parsed_payment_method)
    return payment_methods


def get_response_for_stored_payment_method_request_delete(
    response_data: Optional[dict],
) -> "StoredPaymentMethodRequestDeleteResponseData":
    if response_data is None:
        result = StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER
        error = "Failed to delivery request."
    else:
        try:
            response_result = response_data.get("result") or ""
            result = StoredPaymentMethodRequestDeleteResult[response_result]
            error = response_data.get("error", None)
        except KeyError:
            result = StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE
            error = "Missing or incorrect `result` in response."

    return StoredPaymentMethodRequestDeleteResponseData(
        result=result,
        error=error,
    )


def get_list_stored_payment_methods_data_dict(user_id: int, channel_slug: str):
    return {
        "user_id": graphene.Node.to_global_id("User", user_id),
        "channel_slug": channel_slug,
    }


def invalidate_cache_for_stored_payment_methods(
    user_id: int, channel_slug: str, app_identifier: str
):
    event_type = WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS
    cache_data = get_list_stored_payment_methods_data_dict(user_id, channel_slug)
    webhooks = get_webhooks_for_event(event_type, apps_identifier=[app_identifier])
    for webhook in webhooks:
        cache_key = generate_cache_key_for_webhook(
            cache_data, webhook.target_url, event_type, webhook.app_id
        )
        cache.delete(cache_key)


def get_response_for_payment_gateway_initialize_tokenization(
    response_data: Optional[dict],
) -> "PaymentGatewayInitializeTokenizationResponseData":
    data = None
    if response_data is None:
        result = PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER
        error = "Failed to delivery request."
    else:
        try:
            response_result = response_data.get("result") or ""
            result = PaymentGatewayInitializeTokenizationResult[response_result]
            error = response_data.get("error", None)
            data = response_data.get("data", None)
        except KeyError:
            result = PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE
            error = "Missing or incorrect `result` in response."

    return PaymentGatewayInitializeTokenizationResponseData(
        result=result, error=error, data=data
    )


def get_response_for_payment_method_tokenization(
    response_data: Optional[dict], app: "App"
) -> "PaymentMethodTokenizationResponseData":
    data = None
    payment_method_id = None
    if response_data is None:
        result = PaymentMethodTokenizationResult.FAILED_TO_DELIVER
        error = "Failed to delivery request."
    else:
        try:
            response_result = response_data.get("result") or ""
            result = PaymentMethodTokenizationResult[response_result]
            error = response_data.get("error", None)
            data = response_data.get("data", None)
        except KeyError:
            result = PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE
            error = "Missing or incorrect `result` in response."

        try:
            payment_method_id = response_data["id"]
            payment_method_id = to_payment_app_id(app, payment_method_id)
        except KeyError:
            if result in [
                PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED,
                PaymentMethodTokenizationResult.ADDITIONAL_ACTION_REQUIRED,
            ]:
                result = PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE
                error = "Missing payment method `id` in response."

    return PaymentMethodTokenizationResponseData(
        result=result, error=error, data=data, id=payment_method_id
    )
