from collections.abc import Iterable
from datetime import datetime
from typing import Any, Optional, Union

from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from graphql import get_default_backend, parse
from graphql.error import GraphQLError
from promise import Promise

from ...account.models import User
from ...app.models import App
from ...core.exceptions import PermissionDenied
from ...core.utils import get_domain
from ...webhook.models import Webhook
from ..core import SaleorContext
from ..core.dataloaders import DataLoader
from ..utils import format_error

logger = get_task_logger(__name__)


def initialize_request(
    requestor=None,
    sync_event=False,
    allow_replica=False,
    event_type: Optional[str] = None,
    request_time: Optional[datetime] = None,
    dataloaders: Optional[dict] = None,
) -> SaleorContext:
    """Prepare a request object for webhook subscription.

    It creates a dummy request object.

    return: HttpRequest
    """
    if dataloaders is None:
        dataloaders = {}
    request = SaleorContext(dataloaders=dataloaders)
    request.path = "/graphql/"
    request.path_info = "/graphql/"
    request.method = "GET"
    request.META = {"SERVER_NAME": SimpleLazyObject(get_domain), "SERVER_PORT": "80"}
    if settings.ENABLE_SSL:
        request.META["HTTP_X_FORWARDED_PROTO"] = "https"
        request.META["SERVER_PORT"] = "443"

    setattr(request, "sync_event", sync_event)
    setattr(request, "event_type", event_type)
    request.requestor = requestor
    request.request_time = request_time or timezone.now()
    request.allow_replica = allow_replica

    return request


def get_event_payload(event):
    # Queries that use dataloaders return Promise object for the "event" field. In that
    # case, we need to resolve them first.
    if isinstance(event, Promise):
        return event.get()
    return event


def generate_payload_from_subscription(
    event_type: str,
    subscribable_object,
    subscription_query: str,
    request: SaleorContext,
    app: Optional[App] = None,
) -> Optional[dict[str, Any]]:
    """Generate webhook payload from subscription query.

    It uses a graphql's engine to build payload by using the same logic as response.
    As an input it expects given event type and object and the query which will be
    used to resolve a payload.
    event_type: is an event which will be triggered.
    subscribable_object: is an object which have a dedicated own type in Subscription
    definition.
    subscription_query: query used to prepare a payload via graphql engine.
    context: A dummy request used to share context between apps in order to use
    dataloaders benefits.
    app: the owner of the given payload. Required in case when webhook contains
    protected fields.
    return: A payload ready to send via webhook. None if the function was not able to
    generate a payload
    """
    from ..api import schema
    from ..context import get_context_value

    graphql_backend = get_default_backend()
    ast = parse(subscription_query)
    document = graphql_backend.document_from_string(
        schema,
        ast,
    )
    app_id = app.pk if app else None
    request.app = app
    results = document.execute(
        allow_subscriptions=True,
        root=(event_type, subscribable_object),
        context=get_context_value(request),
    )
    if hasattr(results, "errors"):
        logger.warning(
            "Unable to build a payload for subscription. \n" "error: %s",
            str(results.errors),
            extra={"query": subscription_query, "app": app_id},
        )
        return None

    payload: list[Any] = []
    results.subscribe(payload.append)

    if not payload:
        logger.warning(
            "Subscription did not return a payload.",
            extra={"query": subscription_query, "app": app_id},
        )
        return None

    payload_instance = payload[0]
    event_payload = get_event_payload(payload_instance.data.get("event"))

    if payload_instance.errors:
        event_payload["errors"] = [
            format_error(error, (GraphQLError, PermissionDenied))
            for error in payload_instance.errors
        ]

    return event_payload


def get_pre_save_payload_key(webhook, instance):
    return f"{webhook.pk}_{instance.pk}"


def generate_pre_save_payloads(
    webhooks: Iterable[Webhook],
    instances: Iterable[models.Model],
    event_type: str,
    requestor: Union[User, App, None],
    request_time: datetime,
):
    if not settings.ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS:
        return {}

    pre_save_payloads = {}

    # Dataloaders are shared between calls to generate_payload_from_subscription to
    # reuse their cache. This avoids unnecessary DB queries when different webhooks
    # need to resolve the same data.
    dataloaders: dict[str, type[DataLoader]] = {}

    request = initialize_request(
        requestor=requestor,
        sync_event=False,
        allow_replica=True,
        event_type=event_type,
        request_time=request_time,
        dataloaders=dataloaders,
    )

    for webhook in webhooks:
        if not webhook.subscription_query:
            continue

        for instance in instances:
            instance_payload = generate_payload_from_subscription(
                event_type=event_type,
                subscribable_object=instance,
                subscription_query=webhook.subscription_query,
                request=request,
                app=webhook.app,
            )
            key = get_pre_save_payload_key(webhook, instance)
            pre_save_payloads[key] = instance_payload

    return pre_save_payloads
