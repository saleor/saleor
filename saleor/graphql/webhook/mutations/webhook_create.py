from typing import Optional

import graphene
from django.core.exceptions import ValidationError

from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AppPermission
from ....webhook import models
from ....webhook.error_codes import WebhookErrorCode
from ....webhook.validators import (
    HEADERS_LENGTH_LIMIT,
    HEADERS_NUMBER_LIMIT,
    custom_headers_validator,
)
from ...app.dataloaders import get_app_promise
from ...app.utils import validate_app_is_not_removed
from ...core import ResolveInfo
from ...core.descriptions import (
    ADDED_IN_32,
    ADDED_IN_312,
    DEPRECATED_IN_3X_INPUT,
    PREVIEW_FEATURE,
)
from ...core.doc_category import DOC_CATEGORY_WEBHOOKS
from ...core.fields import JSONString
from ...core.mutations import ModelMutation
from ...core.types import BaseInputObjectType, NonNullList, WebhookError
from ...core.utils import raise_validation_error
from .. import enums
from ..mixins import NotifyUserEventValidationMixin
from ..subscription_query import SubscriptionQuery
from ..types import Webhook


class WebhookCreateInput(BaseInputObjectType):
    name = graphene.String(description="The name of the webhook.", required=False)
    target_url = graphene.String(description="The url to receive the payload.")
    events = NonNullList(
        enums.WebhookEventTypeEnum,
        description=(
            f"The events that webhook wants to subscribe. {DEPRECATED_IN_3X_INPUT} "
            "Use `asyncEvents` or `syncEvents` instead."
        ),
    )
    async_events = NonNullList(
        enums.WebhookEventTypeAsyncEnum,
        description="The asynchronous events that webhook wants to subscribe.",
    )
    sync_events = NonNullList(
        enums.WebhookEventTypeSyncEnum,
        description="The synchronous events that webhook wants to subscribe.",
    )
    app = graphene.ID(
        required=False,
        description="ID of the app to which webhook belongs.",
    )
    is_active = graphene.Boolean(
        description="Determine if webhook will be set active or not.", required=False
    )
    secret_key = graphene.String(
        description="The secret key used to create a hash signature with each payload."
        f"{DEPRECATED_IN_3X_INPUT} As of Saleor 3.5, webhook payloads default to "
        "signing using a verifiable JWS.",
        required=False,
    )
    query = graphene.String(
        description="Subscription query used to define a webhook payload."
        + ADDED_IN_32,
        required=False,
    )
    custom_headers = JSONString(
        description=f"Custom headers, which will be added to HTTP request. "
        f"There is a limitation of {HEADERS_NUMBER_LIMIT} headers per webhook "
        f"and {HEADERS_LENGTH_LIMIT} characters per header."
        f"Only `X-*`, `Authorization*`, and `BrokerProperties` keys are allowed."
        + ADDED_IN_312
        + PREVIEW_FEATURE,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS


class WebhookCreate(ModelMutation, NotifyUserEventValidationMixin):
    class Arguments:
        input = WebhookCreateInput(
            description="Fields required to create a webhook.", required=True
        )

    class Meta:
        description = "Creates a new webhook subscription."
        model = models.Webhook
        object_type = Webhook
        permissions = (
            AppPermission.MANAGE_APPS,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        error_type_class = WebhookError
        error_type_field = "webhook_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_data = super().clean_input(info, instance, data, **kwargs)
        app = cleaned_data.get("app")

        # We are not able to check it in `check_permission`.
        # We need to confirm that cleaned_data has app_id or
        # context has assigned app instance
        if not instance.app_id and not app:
            raise ValidationError(
                "Missing app id. Fill in the app field or run the mutation by the app",
                code=WebhookErrorCode.INVALID.value,
            )

        if instance.app_id:
            # Let's skip app id in case when context has
            # app instance
            app = instance.app
            cleaned_data.pop("app", None)

        validate_app_is_not_removed(app, data.get("input", {}).get("app"), "app")
        if not app or not app.is_active:
            raise ValidationError(
                "App doesn't exist or is disabled",
                code=WebhookErrorCode.NOT_FOUND.value,
            )

        subscription_query = None
        if query := cleaned_data.get("query"):
            subscription_query = SubscriptionQuery(query)
            if not subscription_query.is_valid:
                raise_validation_error(
                    field="query",
                    message=subscription_query.error_msg,
                    code=subscription_query.error_code,
                )
            instance.subscription_query = query

        if headers := cleaned_data.get("custom_headers"):
            try:
                cleaned_data["custom_headers"] = custom_headers_validator(headers)
            except ValidationError as err:
                raise_validation_error(
                    field="customHeaders",
                    message=err.message,
                    code=WebhookErrorCode.INVALID_CUSTOM_HEADERS,
                )

        cls._clean_webhook_events(cleaned_data, subscription_query)

        return cleaned_data

    @classmethod
    def _clean_webhook_events(
        cls, data, subscription_query: Optional[SubscriptionQuery]
    ):
        # if `events` field is not empty, use this field. Otherwise get event types
        # from `async_events` and `sync_events`. If the fields are also empty,
        # parse events from `query`.
        events = data.get("events", [])
        if not events:
            events += data.pop("async_events", [])
            events += data.pop("sync_events", [])

        if not events and subscription_query:
            events = subscription_query.events
        cls.validate_events(events)

        data["events"] = events
        return data

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        instance = super().get_instance(info, **data)
        app = get_app_promise(info.context).get()
        instance.app = app
        return instance

    @classmethod
    def save(cls, _info: ResolveInfo, instance, cleaned_input):
        instance.save()
        events = set(cleaned_input.get("events", []))
        models.WebhookEvent.objects.bulk_create(
            [
                models.WebhookEvent(webhook=instance, event_type=event)
                for event in events
            ]
        )
