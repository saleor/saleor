import logging
from typing import TYPE_CHECKING, Any, Union

from django.conf import settings
from promise import Promise

from ...app.models import App
from ...core.taxes import TaxData, TaxDataError
from ...webhook.transport.synchronous.transport import (
    trigger_webhook_sync_promise,
)
from ...webhook.utils import get_webhooks_for_event
from .parser import parse_tax_data

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App
    from ...checkout.models import Checkout
    from ...order.models import Order

logger = logging.getLogger(__name__)


def get_taxes(
    taxable_object: Union["Checkout", "Order"],
    event_type: str,
    app_identifier: str | None,
    static_payload: str,
    lines_count: int,
    requestor: Union["App", "User", None],
) -> Promise[TaxData | None]:
    if app_identifier:
        return get_taxes_for_app_identifier(
            event_type=event_type,
            app_identifier=app_identifier,
            expected_lines_count=lines_count,
            subscribable_object=taxable_object,
            requestor=requestor,
            static_payload=static_payload,
        )
    return get_taxes_from_all_webhooks(
        event_type=event_type,
        expected_lines_count=lines_count,
        static_payload=static_payload,
        subscribable_object=taxable_object,
        requestor=requestor,
    )


def get_taxes_for_app_identifier(
    event_type: str,
    app_identifier: str,
    static_payload: str,
    expected_lines_count: int,
    subscribable_object: Union["Checkout", "Order"],
    requestor: Union["App", "User", None],
) -> Promise[TaxData | None]:
    app = (
        App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(
            identifier=app_identifier,
            is_active=True,
        )
        .order_by("-created_at")
        .first()
    )

    if app is None:
        msg = "Configured tax app doesn't exist."
        logger.warning(msg)
        return Promise.reject(TaxDataError(msg))

    webhook = get_webhooks_for_event(event_type, apps_ids=[app.id]).first()
    if webhook is None:
        msg = "Configured tax app's webhook for taxes calculation doesn't exists."
        logger.warning(msg)
        return Promise.reject(TaxDataError(msg))

    tax_webhook_promise = trigger_webhook_sync_promise(
        event_type=event_type,
        webhook=webhook,
        static_payload=static_payload,
        allow_replica=False,
        subscribable_object=subscribable_object,
        requestor=requestor,
    )

    def process_response(response_data):
        try:
            tax_data = parse_tax_data(event_type, response_data, expected_lines_count)
            return Promise.resolve(tax_data)
        except TaxDataError as e:
            return Promise.reject(e)

    return tax_webhook_promise.then(process_response)


def get_taxes_from_all_webhooks(
    event_type: str,
    static_payload: str,
    expected_lines_count: int,
    subscribable_object: Union["Checkout", "Order"],
    requestor: Union["App", "User", None],
) -> Promise[TaxData | None]:
    webhooks = get_webhooks_for_event(event_type)

    logger.warning(
        "Missing tax configuration for channel: %s. All tax sync webhooks "
        "will be triggered. This will stop working in future releases. "
        "Make sure to configure tax webhooks for each channel.",
        subscribable_object.channel.slug,
    )

    tax_webhook_promises = []
    for webhook in webhooks:
        tax_webhook_promises.append(
            trigger_webhook_sync_promise(
                event_type=event_type,
                webhook=webhook,
                static_payload=static_payload,
                allow_replica=False,
                subscribable_object=subscribable_object,
                requestor=requestor,
            )
        )

    def process_responses(response_data: list[Any]) -> TaxData | None:
        for response in response_data:
            try:
                parsed_response = parse_tax_data(
                    event_type, response, expected_lines_count
                )
                return parsed_response

            except TaxDataError:
                continue
        return None

    return Promise.all(tax_webhook_promises).then(process_responses)
