import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Union

from django.conf import settings
from promise import Promise

from ..shipping.interface import ShippingMethodData
from ..shipping.models import ShippingMethod, ShippingMethodChannelListing
from ..shipping.utils import (
    convert_to_shipping_method_data,
    initialize_shipping_method_active_status,
)
from ..warehouse.models import Warehouse
from . import (
    ORDER_EDITABLE_STATUS,
)
from .models import Order, OrderLine

if TYPE_CHECKING:
    from ..account.models import User
    from ..app.models import App

logger = logging.getLogger(__name__)


PRIVATE_META_APP_SHIPPING_ID = "external_app_shipping_id"


def get_all_shipping_methods_for_order(
    order: Order,
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> list[ShippingMethodData]:
    if not order.is_shipping_required(
        database_connection_name=database_connection_name
    ):
        return []

    shipping_address = order.shipping_address
    if not shipping_address:
        return []

    all_methods = []

    shipping_methods = (
        ShippingMethod.objects.using(database_connection_name)
        .applicable_shipping_methods_for_instance(
            order,
            channel_id=order.channel_id,
            price=order.subtotal.gross,
            shipping_address=shipping_address,
            country_code=shipping_address.country.code,
            database_connection_name=database_connection_name,
        )
        .prefetch_related("channel_listings")
    )

    listing_map = {
        listing.shipping_method_id: listing for listing in shipping_channel_listings
    }

    for method in shipping_methods:
        listing = listing_map.get(method.id)
        if listing:
            shipping_method_data = convert_to_shipping_method_data(method, listing)
            all_methods.append(shipping_method_data)
    return all_methods


def get_valid_shipping_methods_for_order(
    order: Order,
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"],
    requestor: Union["App", "User", None],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[list[ShippingMethodData]]:
    """Return a list of shipping methods according to Saleor's own business logic."""

    # Circular import caused by the current definition of subscription payloads
    # and their usage in webhook/transport layer. Until moving them out from the
    # transport, we will have circular imports.
    from .webhooks.exclude_shipping import (
        ExcludedShippingMethod,
        excluded_shipping_methods_for_order,
    )

    valid_methods = get_all_shipping_methods_for_order(
        order, shipping_channel_listings, database_connection_name
    )
    if not valid_methods:
        return Promise.resolve([])

    allow_replica = True
    if database_connection_name == settings.DATABASE_CONNECTION_DEFAULT_NAME:
        allow_replica = False

    promised_excluded_methods: Promise[list[ExcludedShippingMethod]] = Promise.resolve(
        []
    )
    if order.status in ORDER_EDITABLE_STATUS and allow_sync_webhooks:
        promised_excluded_methods = excluded_shipping_methods_for_order(
            order, valid_methods, allow_replica=allow_replica, requestor=requestor
        )

    def handle_excluded_methods(excluded_methods):
        initialize_shipping_method_active_status(valid_methods, excluded_methods)
        return valid_methods

    return promised_excluded_methods.then(handle_excluded_methods)


def get_external_shipping_id(order: "Order"):
    if not order:
        return None
    return order.get_value_from_private_metadata(PRIVATE_META_APP_SHIPPING_ID)


def is_shipping_required(lines: Iterable["OrderLine"]):
    return any(line.is_shipping_required for line in lines)


def get_valid_collection_points_for_order(
    lines: Iterable["OrderLine"],
    channel_id: int,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    if not is_shipping_required(lines):
        return []

    line_ids = [line.id for line in lines]
    qs = OrderLine.objects.using(database_connection_name).filter(id__in=line_ids)

    return Warehouse.objects.using(
        database_connection_name
    ).applicable_for_click_and_collect(qs, channel_id)
