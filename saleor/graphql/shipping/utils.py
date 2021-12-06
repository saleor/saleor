from typing import TYPE_CHECKING, List, Optional

from ...account.models import Address
from ...plugins.base_plugin import ExcludedShippingMethod
from ...plugins.base_plugin import ShippingMethod as ShippingMethodDataclass
from ...shipping import models as shipping_models
from ..channel import ChannelContext

if TYPE_CHECKING:
    from ...plugins.manager import PluginsManager
    from ...shipping.models import ShippingMethodChannelListing


def convert_shipping_method_model_to_dataclass(
    shipping_method: shipping_models.ShippingMethod,
):
    shipping_method_dataclass = ShippingMethodDataclass(
        id=str(shipping_method.id),
        price=shipping_method.price,  # type: ignore
        name=shipping_method.name,
        maximum_delivery_days=shipping_method.maximum_delivery_days,
        minimum_delivery_days=shipping_method.minimum_delivery_days,
        maximum_order_weight=None,
        minimum_order_weight=None,
    )
    shipping_method_dataclass.maximum_order_weight = (
        shipping_method.maximum_order_weight
    )
    shipping_method_dataclass.minimum_order_weight = (
        shipping_method.minimum_order_weight
    )
    return shipping_method_dataclass


def annotate_shipping_methods_with_price(
    shipping_methods: List[shipping_models.ShippingMethod],
    channel_listings: List["ShippingMethodChannelListing"],
    address: Optional["Address"],
    channel_slug: str,
    manager: "PluginsManager",
):
    if not address:
        return
    channel_listing_map = {
        channel_listing.shipping_method_id: channel_listing
        for channel_listing in channel_listings
    }
    for method in shipping_methods:
        shipping_channel_listing = channel_listing_map[method.id]
        method.price = shipping_channel_listing.price  # type: ignore


def annotate_active_shipping_methods(
    shipping_methods: List[shipping_models.ShippingMethod],
    excluded_methods: List[ExcludedShippingMethod],
):
    for instance in shipping_methods:
        instance.active = True  # type: ignore
        instance.message = ""  # type: ignore
        for method in excluded_methods:
            if str(instance.id) == str(method.id):
                instance.active = False  # type: ignore
                instance.message = method.reason  # type: ignore


def wrap_with_channel_context(
    shipping_methods: List[shipping_models.ShippingMethod],
    channel_slug: str,
) -> List[ChannelContext]:
    instances = [
        ChannelContext(
            node=method,
            channel_slug=channel_slug,
        )
        for method in shipping_methods
    ]
    return instances
