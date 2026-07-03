import json
import logging
from typing import TYPE_CHECKING, Union

from promise import Promise

from ...core.db.connection import allow_writer
from ...core.prices import quantize_price
from ...core.utils.json_serializer import CustomJsonEncoder
from ...shipping.interface import ExcludedShippingMethod, ShippingMethodData
from ...shipping.webhooks.shared import (
    generate_payload_for_shipping_method,
    get_excluded_shipping_data,
)
from ...webhook import traced_payload_generator
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.payloads import (
    generate_order_payload,
)
from ...webhook.utils import get_webhooks_for_event

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App
    from ...order.models import Order


logger = logging.getLogger(__name__)


@allow_writer()
@traced_payload_generator
def generate_excluded_shipping_methods_for_order_payload(
    order: "Order",
    available_shipping_methods: list[ShippingMethodData],
):
    order_data = json.loads(generate_order_payload(order))[0]
    payload = {
        "order": order_data,
        "shipping_methods": [
            generate_payload_for_shipping_method(shipping_method)
            for shipping_method in available_shipping_methods
        ],
    }
    return json.dumps(payload, cls=CustomJsonEncoder)


def excluded_shipping_methods_for_order(
    order: "Order",
    available_shipping_methods: list["ShippingMethodData"],
    allow_replica: bool,
    requestor: Union["App", "User", None],
) -> Promise[list[ExcludedShippingMethod]]:
    if not available_shipping_methods:
        return Promise.resolve([])

    webhooks = get_webhooks_for_event(
        WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
    )
    if not webhooks:
        return Promise.resolve([])

    static_payload = generate_excluded_shipping_methods_for_order_payload(
        order,
        available_shipping_methods,
    )
    cache_data = _get_cache_data_for_exclude_shipping_methods(order, static_payload)
    return get_excluded_shipping_data(
        webhooks=webhooks,
        event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
        static_payload=static_payload,
        subscribable_object=(order, available_shipping_methods),
        allow_replica=allow_replica,
        requestor=requestor,
        cache_data=cache_data,
    )


def _get_cache_data_for_exclude_shipping_methods(order: "Order", payload: str) -> dict:
    payload_dict = json.loads(payload)
    source_object = payload_dict.get("order", {})

    # Drop fields that can be set by tax-app
    order_fields_to_drop = [
        "shipping_price_gross_amount",
        "shipping_price_net_amount",
        "total_net_amount",
        "total_gross_amount",
        "shipping_tax_rate",
        "undiscounted_total_net_amount",
        "undiscounted_total_gross_amount",
    ]
    line_fields_to_drop = [
        "undiscounted_unit_price_gross_amount",
        "undiscounted_unit_price_net_amount",
        "undiscounted_total_price_net_amount",
        "undiscounted_total_price_gross_amount",
        "unit_price_net_amount",
        "unit_price_gross_amount",
        "tax_rate",
        "total_price_net_amount",
        "total_price_gross_amount",
    ]

    for field in order_fields_to_drop:
        source_object.pop(field, None)

    source_object["base_shipping_price_amount"] = str(
        quantize_price(order.base_shipping_price_amount, order.currency)
    )
    source_object["lines_pricing"] = [
        {
            "base_unit_price_amount": str(
                quantize_price(order_line.base_unit_price_amount, order.currency)
            ),
        }
        for order_line in order.lines.all()
    ]

    lines_list = source_object.get("lines", [])
    for line in lines_list:
        for field in line_fields_to_drop:
            line.pop(field, None)

    # drop fields that change between requests but are not relevant for cache key
    source_object.pop("last_change", None)
    source_object.pop("meta", None)
    source_object.pop("shipping_method", None)
    return payload_dict
