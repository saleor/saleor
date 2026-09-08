import graphene
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Exists, OuterRef

from ....app.models import App
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AppPermission
from ....webhook import models
from ....webhook.error_codes import WebhookErrorCode
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_323
from ...core.mutations import ModelDeleteMutation
from ...core.types import WebhookError
from ..types import Webhook
from .utils import get_webhook_object_id


class WebhookDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=False,
            description=(
                "ID of a webhook to delete. Cannot be used together with `identifier`."
            ),
        )
        identifier = graphene.String(
            required=False,
            description=(
                "App-provided identifier of a webhook to delete. Identifiers are "
                "unique per app only, so this argument is available exclusively to an "
                "app referencing its own webhook; staff users must use `id`. Cannot "
                "be used together with `id`." + ADDED_IN_323
            ),
        )

    class Meta:
        description = (
            "Deletes a webhook. Before the deletion, the webhook is deactivated to "
            "pause any deliveries that are already scheduled. The deletion might fail "
            "if delivery is in progress. In such a case, the webhook is not deleted "
            "but remains deactivated."
        )
        model = models.Webhook
        object_type = Webhook
        permissions = (
            AppPermission.MANAGE_APPS,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        error_type_class = WebhookError
        error_type_field = "webhook_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        app = get_app_promise(info.context).get()
        if app and not app.is_active:
            raise ValidationError(
                "App needs to be active to delete webhook",
                code=WebhookErrorCode.INVALID.value,
            )
        node_id = get_webhook_object_id(
            app=app,
            object_id=data.get("id"),
            identifier=data.pop("identifier", None),
        )
        data["id"] = node_id
        apps = App.objects.filter(removed_at__isnull=True)
        webhook = cls.get_node_or_error(
            info,
            node_id,
            only_type=Webhook,
            qs=models.Webhook.objects.filter(
                Exists(apps.filter(id=OuterRef("app_id")))
            ),
        )
        if app and webhook.app_id != app.id:
            raise ValidationError(
                f"Couldn't resolve to a node: {node_id}",
                code=WebhookErrorCode.GRAPHQL_ERROR.value,
            )
        webhook.is_active = False
        webhook.save(update_fields=["is_active"])

        try:
            response = super().perform_mutation(_root, info, **data)
        except IntegrityError as e:
            raise ValidationError(
                "Webhook couldn't be deleted at this time due to running task."
                "Webhook deactivated. Try deleting Webhook later",
                code=WebhookErrorCode.DELETE_FAILED.value,
            ) from e

        return response
