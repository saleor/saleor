from typing import List

from ...plugins.base_plugin import ExcludedShippingMethod
from ...shipping import models as shipping_models
from ...shipping.interface import ShippingMethodData
from ..channel import ChannelContext


def annotate_active_shipping_methods(
    shipping_methods: List[ShippingMethodData],
    excluded_methods: List[ExcludedShippingMethod],
):
    """Assign availability status based on the response from plugins."""
    for instance in shipping_methods:
        instance.active = True
        instance.message = ""
        for method in excluded_methods:
            if str(instance.id) == str(method.id):
                instance.active = False
                instance.message = method.reason or ""


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
