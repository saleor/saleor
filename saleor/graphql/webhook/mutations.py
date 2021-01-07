import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import AppPermission
from ...webhook import models
from ...webhook.error_codes import WebhookErrorCode
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import WebhookError
from .enums import WebhookEventTypeEnum


class WebhookCreateInput(graphene.InputObjectType):
    name = graphene.String(description="The name of the webhook.", required=False)
    target_url = graphene.String(description="The url to receive the payload.")
    events = graphene.List(
        WebhookEventTypeEnum,
        description=(
            "The events that webhook wants to subscribe. The CHECKOUT_QUANTITY_CHANGED"
            " is deprecated. It will be removed in Saleor 3.0"
        ),
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


class WebhookCreate(ModelMutation):
    class Arguments:
        input = WebhookCreateInput(
            description="Fields required to create a webhook.", required=True
        )

    class Meta:
        description = "Creates a new webhook subscription."
        model = models.Webhook
        permissions = (AppPermission.MANAGE_APPS,)
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
        return cleaned_data

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        app = info.context.app
        instance.app = app
        return instance

    @classmethod
    def check_permissions(cls, context):
        has_perm = super().check_permissions(context)
        has_perm = bool(context.app) or has_perm
        return has_perm

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
    events = graphene.List(
        WebhookEventTypeEnum,
        description=(
            "The events that webhook wants to subscribe. The CHECKOUT_QUANTITY_CHANGED"
            " is deprecated. It will be removed in Saleor 3.0"
        ),
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


class WebhookUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a webhook to update.")
        input = WebhookUpdateInput(
            description="Fields required to update a webhook.", required=True
        )

    class Meta:
        description = "Updates a webhook subscription."
        model = models.Webhook
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
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = WebhookError
        error_type_field = "webhook_errors"

    @classmethod
    def check_permissions(cls, context):
        has_perm = super().check_permissions(context)
        has_perm = bool(context.app) or has_perm
        return has_perm

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id = data["id"]
        _, object_id = graphene.Node.from_global_id(node_id)

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
