import graphene
from django.db.models import Exists, OuterRef

from ....app.models import App
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AppPermission
from ....webhook import models
from ....webhook.validators import HEADERS_LENGTH_LIMIT, HEADERS_NUMBER_LIMIT
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_WEBHOOKS
from ...core.fields import JSONString
from ...core.types import BaseInputObjectType, NonNullList, WebhookError
from .. import enums
from ..mixins import NotifyUserEventValidationMixin
from ..types import Webhook
from . import WebhookCreate


class WebhookUpdateInput(BaseInputObjectType):
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
        description="Use to create a hash signature with each payload."
        f"{DEPRECATED_IN_3X_INPUT} As of Saleor 3.5, webhook payloads default to "
        "signing using a verifiable JWS.",
        required=False,
    )
    query = graphene.String(
        description="Subscription query used to define a webhook payload.",
        required=False,
    )
    custom_headers = JSONString(
        description=f"Custom headers, which will be added to HTTP request. "
        f"There is a limitation of {HEADERS_NUMBER_LIMIT} headers per webhook "
        f"and {HEADERS_LENGTH_LIMIT} characters per header."
        f"Only `X-*`, `Authorization*`, and `BrokerProperties` keys are allowed.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS


class WebhookUpdate(WebhookCreate, NotifyUserEventValidationMixin):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a webhook to update.")
        input = WebhookUpdateInput(
            description="Fields required to update a webhook.", required=True
        )

    class Meta:
        description = "Updates a webhook subscription."
        model = models.Webhook
        object_type = Webhook
        permissions = (
            AppPermission.MANAGE_APPS,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        error_type_class = WebhookError
        error_type_field = "webhook_errors"

    @classmethod
    def save(cls, _info: ResolveInfo, instance, cleaned_input, instance_tracker=None):
        instance.save()
        events = set(cleaned_input.get("events", []))
        cls.validate_events(events)
        if events:
            instance.events.all().delete()
            models.WebhookEvent.objects.bulk_create(
                [
                    models.WebhookEvent(webhook=instance, event_type=event)
                    for event in events
                ]
            )

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        apps = App.objects.filter(removed_at__isnull=True)
        if app := get_app_promise(info.context).get():
            apps = apps.filter(id=app.id)
        data["qs"] = models.Webhook.objects.filter(
            Exists(apps.filter(id=OuterRef("app_id")))
        )
        return super(WebhookCreate, cls).get_instance(info, **data)
