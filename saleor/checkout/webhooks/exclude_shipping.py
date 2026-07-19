import json
import logging
from typing import TYPE_CHECKING, Union

from promise import Promise

from ...core.db.connection import allow_writer
from ...core.utils.json_serializer import CustomJsonEncoder
from ...shipping.interface import ExcludedShippingMethod, ShippingMethodData
from ...shipping.webhooks.shared import (
    generate_payload_for_shipping_method,
    get_excluded_shipping_data,
)
from ...webhook import traced_payload_generator
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.payloads import (
    generate_checkout_payload,
)
from ...webhook.utils import get_webhooks_for_event
from ..models import Checkout

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App

logger = logging.getLogger(__name__)


def excluded_shipping_methods_for_checkout(
    checkout: "Checkout",
    available_shipping_methods: list["ShippingMethodData"],
    allow_replica: bool,
    requestor: Union["App", "User", None],
) -> Promise[list[ExcludedShippingMethod]]:
    if not available_shipping_methods:
        return Promise.resolve([])

    webhooks = get_webhooks_for_event(
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )
    if not webhooks:
        return Promise.resolve([])

    static_payload = _generate_excluded_shipping_methods_for_checkout_payload(
        checkout,
        available_shipping_methods,
    )
    return get_excluded_shipping_data(
        webhooks=webhooks,
        event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
        static_payload=static_payload,
        subscribable_object=(checkout, available_shipping_methods),
        allow_replica=allow_replica,
        requestor=requestor,
        # Set cache to None as Checkout doesn't use cache flow anymore
        # This field will be fully dropped after moving Order to new
        # flow.
        cache_data=None,
    )


@allow_writer()
@traced_payload_generator
def _generate_excluded_shipping_methods_for_checkout_payload(
    checkout: "Checkout",
    available_shipping_methods: list[ShippingMethodData],
):
    checkout_data = json.loads(generate_checkout_payload(checkout))[0]
    payload = {
        "checkout": checkout_data,
        "shipping_methods": [
            generate_payload_for_shipping_method(shipping_method)
            for shipping_method in available_shipping_methods
        ],
    }
    return json.dumps(payload, cls=CustomJsonEncoder)
