import logging
from typing import cast

import graphene
from django.core.cache import cache
from pydantic import ValidationError

from ...app.models import App
from ...payment.interface import (
    JSONValue,
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
from ..response_schemas.payment import (
    ListStoredPaymentMethodsSchema,
    PaymentGatewayInitializeTokenizationSessionSchema,
    PaymentMethodTokenizationFailedSchema,
    PaymentMethodTokenizationPendingSchema,
    PaymentMethodTokenizationSuccessSchema,
    StoredPaymentMethodDeleteRequestedSchema,
)
from ..response_schemas.utils.helpers import parse_validation_error
from .utils import generate_cache_key_for_webhook, to_payment_app_id

logger = logging.getLogger(__name__)


def get_list_stored_payment_methods_from_response(
    app: "App", response_data: dict, currency: str
) -> list["PaymentMethodData"]:
    try:
        stored_payment_methods_model = ListStoredPaymentMethodsSchema.model_validate(
            response_data,
            context={
                "custom_message": "Skipping invalid stored payment method",
                "app": app,
            },
        )
    except ValidationError as e:
        logger.warning(
            "Skipping stored payment methods from app %s. Error: %s",
            app.id,
            str(e),
            extra={"app": app.id},
        )
        return []

    app_identifier = app.identifier
    return [
        PaymentMethodData(
            id=to_payment_app_id(app, payment_method.id),
            external_id=payment_method.id,
            supported_payment_flows=payment_method.supported_payment_flows,
            type=payment_method.type,
            credit_card_info=PaymentMethodCreditCardInfo(
                **dict(payment_method.credit_card_info),
            )
            if payment_method.credit_card_info
            else None,
            name=payment_method.name,
            data=payment_method.data,  # type: ignore[arg-type]
            gateway=PaymentGateway(
                id=app_identifier, name=app.name, currencies=[currency], config=[]
            ),
        )
        for payment_method in stored_payment_methods_model.payment_methods
    ]


def get_response_for_stored_payment_method_request_delete(
    response_data: dict | None,
) -> "StoredPaymentMethodRequestDeleteResponseData":
    error: str | None = None
    if response_data is None:
        result = StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER
        error = "Failed to delivery request."
    else:
        try:
            delete_requested_model = (
                StoredPaymentMethodDeleteRequestedSchema.model_validate(response_data)
            )
            result = delete_requested_model.result
            error = delete_requested_model.error
        except ValidationError as e:
            result = StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE
            error = parse_validation_error(e)

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
    response_data: dict | None,
) -> "PaymentGatewayInitializeTokenizationResponseData":
    data = None
    error: str | None = None
    if response_data is None:
        result = PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER
        error = "Failed to delivery request."
    else:
        try:
            gateway_initialize_model = (
                PaymentGatewayInitializeTokenizationSessionSchema.model_validate(
                    response_data
                )
            )
            result = gateway_initialize_model.result
            error = gateway_initialize_model.error
            data = gateway_initialize_model.data
        except ValidationError as e:
            result = PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE
            error = parse_validation_error(e)

    data = cast(JSONValue, data)
    return PaymentGatewayInitializeTokenizationResponseData(
        result=result, error=error, data=data
    )


def get_response_for_payment_method_tokenization(
    response_data: dict | None, app: "App"
) -> "PaymentMethodTokenizationResponseData":
    data = None
    error: str | None = None
    payment_method_id = None
    if response_data is None:
        result = PaymentMethodTokenizationResult.FAILED_TO_DELIVER
        error = "Failed to delivery request."
    else:
        try:
            response_model = _validate_payment_method_response(response_data, app)
            result = response_model.result
            error = getattr(response_model, "error", None)
            data = getattr(response_model, "data", None)
            payment_method_id = getattr(response_model, "id", None)
        except ValidationError as e:
            result = PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE
            error = parse_validation_error(e)
        except ValueError as e:
            result = PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE
            error = str(e)

    return PaymentMethodTokenizationResponseData(
        result=result, error=error, data=data, id=payment_method_id
    )


def _validate_payment_method_response(response_data: dict, app):
    context = {
        "app": app,
    }
    match response_data.get("result"):
        case (
            PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name
            | PaymentMethodTokenizationResult.ADDITIONAL_ACTION_REQUIRED.name
        ):
            return PaymentMethodTokenizationSuccessSchema.model_validate(
                response_data, context=context
            )
        case PaymentMethodTokenizationResult.PENDING.name:
            return PaymentMethodTokenizationPendingSchema.model_validate(
                response_data, context=context
            )
        case (
            PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE.name
            | PaymentMethodTokenizationResult.FAILED_TO_DELIVER.name
        ):
            return PaymentMethodTokenizationFailedSchema.model_validate(
                response_data, context=context
            )
        case _:
            possible_values = ", ".join(
                [value.name for value in PaymentMethodTokenizationResult]
            )
            logger.warning(
                "Invalid value for `result`: %s. Possible values: %s.",
                response_data.get("result"),
                possible_values,
                extra={"app": app.id},
            )
            raise ValueError(
                f"Missing or invalid value for `result`: {response_data.get('result')}. Possible values: {possible_values}."
            )
