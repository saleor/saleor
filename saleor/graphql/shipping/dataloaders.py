from collections import defaultdict

from django.db.models import F

from ...shipping.models import (
    ShippingMethod,
    ShippingMethodChannelListing,
    ShippingMethodPostalCodeRule,
)
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


class PostalCodeRulesByShippingMethodIdLoader(DataLoader):
    context_key = "postal_code_rules_by_shipping_method"

    def batch_load(self, keys):
        postal_code_rules = ShippingMethodPostalCodeRule.objects.filter(
            shipping_method_id__in=keys
        )

        postal_code_rules_map = defaultdict(list)
        for postal_code in postal_code_rules:
            postal_code_rules_map[postal_code.shipping_method_id].append(postal_code)
        return [
            postal_code_rules_map[shipping_method_id] for shipping_method_id in keys
        ]


class ShippingMethodsByShippingZoneIdAndChannelSlugLoader(DataLoader):
    context_key = "shippingmethod_by_shippingzone_and_channel"

    def batch_load(self, keys):
        shipping_methods = ShippingMethod.objects.filter(
            shipping_zone_id__in=keys
        ).annotate(channel_slug=F("channel_listings__channel__slug"))

        shipping_methods_by_shipping_zone_and_channel_map = defaultdict(list)
        for shipping_method in shipping_methods:
            key = (shipping_method.shipping_zone_id, shipping_method.channel_slug)
            shipping_methods_by_shipping_zone_and_channel_map[key].append(
                shipping_method
            )
        return [shipping_methods_by_shipping_zone_and_channel_map[key] for key in keys]


class ShippingMethodChannelListingByShippingMethodIdLoader(DataLoader):
    context_key = "shippingmethodchannellisting_by_shippingmethod"

    def batch_load(self, keys):
        shipping_method_channel_listings = ShippingMethodChannelListing.objects.filter(
            shipping_method_id__in=keys
        )
        shipping_method_channel_listings_by_shipping_method_map = defaultdict(list)
        for shipping_method_channel_listing in shipping_method_channel_listings:
            shipping_method_channel_listings_by_shipping_method_map[
                shipping_method_channel_listing.shipping_method_id
            ].append(shipping_method_channel_listing)
        return [
            shipping_method_channel_listings_by_shipping_method_map[shipping_method_id]
            for shipping_method_id in keys
        ]


class ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(DataLoader):
    context_key = "shippingmethodchannellisting_by_shippingmethod_and_channel"

    def batch_load(self, keys):
        shipping_method_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        shipping_method_channel_listings = ShippingMethodChannelListing.objects.filter(
            shipping_method_id__in=shipping_method_ids, channel__slug__in=channel_slugs
        ).annotate(channel_slug=F("channel__slug"))
        shipping_method_channel_listings_by_shipping_method_and_channel_map = {}
        for shipping_method_channel_listing in shipping_method_channel_listings:
            key = (
                shipping_method_channel_listing.shipping_method_id,
                shipping_method_channel_listing.channel_slug,
            )
            shipping_method_channel_listings_by_shipping_method_and_channel_map[
                key
            ] = shipping_method_channel_listing
        return [
            shipping_method_channel_listings_by_shipping_method_and_channel_map[key]
            for key in keys
        ]
