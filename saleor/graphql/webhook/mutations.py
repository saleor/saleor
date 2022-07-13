import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import AppPermission, AuthorizationFilters
from ...webhook import models
from ...webhook.error_codes import WebhookErrorCode
from ..core.descriptions import ADDED_IN_32, DEPRECATED_IN_3X_INPUT, PREVIEW_FEATURE
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types import NonNullList, WebhookError
from . import enums
from .subscription_payload import validate_query
from .types import EventDelivery, Webhook


class WebhookCreateInput(graphene.InputObjectType):
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
        description="The secret key used to create a hash signature with each payload.",
        required=False,
    )
    query = graphene.String(
        description="Subscription query used to define a webhook payload."
        + ADDED_IN_32
        + PREVIEW_FEATURE,
        required=False,
    )


def clean_webhook_events(_info, _instance, data):
    # if `events` field is not empty, use this field. Otherwise get event types
    # from `async_events` and `sync_events`.
    events = data.get("events", [])
    if not events:
        events += data.pop("async_events", [])
        events += data.pop("sync_events", [])
    data["events"] = events
    return data


class WebhookCreate(ModelMutation):
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
    def clean_input(cls, info, instance, data):
        cleaned_data = super().clean_input(info, instance, data)
        app = cleaned_data.get("app")

        # We are not able to check it in `check_permission`.
        # We need to confirm that cleaned_data has app_id or
        # context has assigned app instance
        if not instance.app_id and not app:
            raise ValidationError("Missing token or app", code=WebhookErrorCode.INVALID)

        if instance.app_id:
            # Let's skip app id in case when context has
            # app instance
            app = instance.app
            cleaned_data.pop("app", None)

        if not app or not app.is_active:
            raise ValidationError(
                "App doesn't exist or is disabled",
                code=WebhookErrorCode.NOT_FOUND,
            )
        clean_webhook_events(info, instance, cleaned_data)
        if query := cleaned_data.get("query"):
            validate_query(query)
            instance.subscription_query = query
        return cleaned_data

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        app = info.context.app
        instance.app = app
        return instance

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        events = set(cleaned_input.get("events", []))
        models.WebhookEvent.objects.bulk_create(
            [
                models.WebhookEvent(webhook=instance, event_type=event)
                for event in events
            ]
        )


class WebhookUpdateInput(graphene.InputObjectType):
    name = graphene.String(description="The new name of the webhook.", required=False)
    target_url = graphene.String(
        description="The url to receive the payload.", required=False
    )
    events = NonNullList(
        enums.WebhookEventTypeEnum,
        description=(
            f"The events that webhook wants to subscribe. {DEPRECATED_IN_3X_INPUT} "
            "Use `asyncEvents` or `syncEvents` instead."
        ),
        required=False,
    )
    async_events = NonNullList(
        enums.WebhookEventTypeAsyncEnum,
        description="The asynchronous events that webhook wants to subscribe.",
        required=False,
    )
    sync_events = NonNullList(
        enums.WebhookEventTypeSyncEnum,
        description="The synchronous events that webhook wants to subscribe.",
        required=False,
    )
    app = graphene.ID(
        required=False,
        description="ID of the app to which webhook belongs.",
    )
    is_active = graphene.Boolean(
        description="Determine if webhook will be set active or not.", required=False
    )
    secret_key = graphene.String(
        description="Use to create a hash signature with each payload.", required=False
    )
    query = graphene.String(
        description="Subscription query used to define a webhook payload."
        + ADDED_IN_32
        + PREVIEW_FEATURE,
        required=False,
    )


class WebhookUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a webhook to update.")
        input = WebhookUpdateInput(
            description="Fields required to update a webhook.", required=True
        )

    class Meta:
        description = "Updates a webhook subscription."
        model = models.Webhook
        object_type = Webhook
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = WebhookError
        error_type_field = "webhook_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_data = super().clean_input(info, instance, data)
        app = cleaned_data.get("app")

        if not instance.app_id and not app:
            raise ValidationError("Missing token or app", code=WebhookErrorCode.INVALID)

        if instance.app_id:
            # Let's skip app id in case when context has
            # app instance
            app = instance.app
            cleaned_data.pop("app", None)

        if not app or not app.is_active:
            raise ValidationError(
                "App doesn't exist or is disabled",
                code=WebhookErrorCode.NOT_FOUND,
            )
        clean_webhook_events(info, instance, cleaned_data)

        if query := cleaned_data.get("query"):
            validate_query(query)
            instance.subscription_query = query
        return cleaned_data

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        events = set(cleaned_input.get("events", []))
        if events:
            instance.events.all().delete()
            models.WebhookEvent.objects.bulk_create(
                [
                    models.WebhookEvent(webhook=instance, event_type=event)
                    for event in events
                ]
            )


class WebhookDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a webhook to delete.")

    class Meta:
        description = "Deletes a webhook subscription."
        model = models.Webhook
        object_type = Webhook
        permissions = (
            AppPermission.MANAGE_APPS,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        error_type_class = WebhookError
        error_type_field = "webhook_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id = data["id"]
        object_id = cls.get_global_id_or_error(node_id)

        app = info.context.app
        if app:
            if not app.is_active:
                raise ValidationError(
                    "App needs to be active to delete webhook",
                    code=WebhookErrorCode.INVALID,
                )
            try:
                app.webhooks.get(id=object_id)
            except models.Webhook.DoesNotExist:
                raise ValidationError(
                    "Couldn't resolve to a node: %s" % node_id,
                    code=WebhookErrorCode.GRAPHQL_ERROR,
                )

        return super().perform_mutation(_root, info, **data)


class EventDeliveryRetry(BaseMutation):
    delivery = graphene.Field(EventDelivery, description="Event delivery.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the event delivery to retry."
        )

    class Meta:
        description = "Retries event delivery."
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = WebhookError

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        delivery = cls.get_node_or_error(
            info,
            data["id"],
            only_type=EventDelivery,
        )
        manager = info.context.plugins
        manager.event_delivery_retry(delivery)
        return EventDeliveryRetry(delivery=delivery)
