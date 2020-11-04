from collections import defaultdict

from django.db.models import F

from ...shipping.models import ShippingMethod
from ..core.dataloaders import DataLoader


class ShippingMethodByIdLoader(DataLoader):
    context_key = "shippingmethod_by_id"

    def batch_load(self, keys):
        shipping_methods = ShippingMethod.objects.in_bulk(keys)
        return [shipping_methods.get(shipping_method_id) for shipping_method_id in keys]


class ShippingMethodsByShippingZoneIdLoader(DataLoader):
    context_key = "shippingmethod_by_shippingzone"

    def batch_load(self, keys):
        shipping_methods = ShippingMethod.objects.filter(shipping_zone_id__in=keys)
        shipping_methods_by_shipping_zone_map = defaultdict(list)
        for shipping_method in shipping_methods:
            shipping_methods_by_shipping_zone_map[
                shipping_method.shipping_zone_id
            ].append(shipping_method)
        return [
            shipping_methods_by_shipping_zone_map[shipping_zone_id]
            for shipping_zone_id in keys
        ]


class ShippingMethodsByShippingZoneIdAndChannelSlugLoader(DataLoader):
    context_key = "shippingmethod_by_shippingzone_and_channel"

    def batch_load(self, keys):
        shipping_methods = ShippingMethod.objects.filter(
            shipping_zone_id__in=keys
        ).annotate(channel_slug=F("channel_listing__channel__slug"))

        shipping_methods_by_shipping_zone_and_channel_map = defaultdict(list)
        for shipping_method in shipping_methods:
            key = (shipping_method.shipping_zone_id, shipping_method.channel_slug)
            shipping_methods_by_shipping_zone_and_channel_map[key].append(
                shipping_method
            )
        return [shipping_methods_by_shipping_zone_and_channel_map[key] for key in keys]
