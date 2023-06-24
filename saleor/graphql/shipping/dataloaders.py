from collections import defaultdict

from django.db.models import Exists, F, OuterRef

from ...channel.models import Channel
from ...shipping.models import (
    ShippingMethod,
    ShippingMethodChannelListing,
    ShippingMethodPostalCodeRule,
    ShippingZone,
)
from ..core.dataloaders import DataLoader


class ShippingMethodByIdLoader(DataLoader):
    context_key = "shippingmethod_by_id"

    def batch_load(self, keys):
        shipping_methods = ShippingMethod.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [shipping_methods.get(shipping_method_id) for shipping_method_id in keys]


class ShippingZoneByIdLoader(DataLoader):
    context_key = "shippingzone_by_id"

    def batch_load(self, keys):
        shipping_zones = ShippingZone.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [shipping_zones.get(shipping_zone_id) for shipping_zone_id in keys]


class ShippingZonesByChannelIdLoader(DataLoader):
    context_key = "shippingzone_by_channel_id"

    def batch_load(self, keys):
        shipping_zones_channel = ShippingZone.channels.through.objects.using(
            self.database_connection_name
        ).filter(channel_id__in=keys)
        shipping_zones_map = (
            ShippingZone.objects.using(self.database_connection_name)
            .filter(
                Exists(shipping_zones_channel.filter(shippingzone_id=OuterRef("pk")))
            )
            .in_bulk()
        )

        shipping_zones_by_channel_map = defaultdict(list)
        for shipping_zone_id, channel_id in shipping_zones_channel.values_list(
            "shippingzone_id", "channel_id"
        ):
            shipping_zones_by_channel_map[channel_id].append(
                shipping_zones_map[shipping_zone_id]
            )
        return [
            shipping_zones_by_channel_map.get(channel_id, []) for channel_id in keys
        ]


class ShippingMethodsByShippingZoneIdLoader(DataLoader):
    context_key = "shippingmethod_by_shippingzone"

    def batch_load(self, keys):
        shipping_methods = ShippingMethod.objects.using(
            self.database_connection_name
        ).filter(shipping_zone_id__in=keys)
        shipping_methods_by_shipping_zone_map = defaultdict(list)
        for shipping_method in shipping_methods:
            shipping_methods_by_shipping_zone_map[
                shipping_method.shipping_zone_id
            ].append(shipping_method)
        return [
            shipping_methods_by_shipping_zone_map.get(shipping_zone_id, [])
            for shipping_zone_id in keys
        ]


class PostalCodeRulesByShippingMethodIdLoader(DataLoader):
    context_key = "postal_code_rules_by_shipping_method"

    def batch_load(self, keys):
        postal_code_rules = (
            ShippingMethodPostalCodeRule.objects.using(self.database_connection_name)
            .filter(shipping_method_id__in=keys)
            .order_by("id")
        )

        postal_code_rules_map = defaultdict(list)
        for postal_code in postal_code_rules:
            postal_code_rules_map[postal_code.shipping_method_id].append(postal_code)
        return [
            postal_code_rules_map.get(shipping_method_id, [])
            for shipping_method_id in keys
        ]


class ShippingMethodsByShippingZoneIdAndChannelSlugLoader(DataLoader):
    context_key = "shippingmethod_by_shippingzone_and_channel"

    def batch_load(self, keys):
        shipping_zone_ids = [zone_id for (zone_id, _) in keys]
        shipping_methods = (
            ShippingMethod.objects.using(self.database_connection_name)
            .filter(shipping_zone_id__in=shipping_zone_ids)
            .annotate(channel_slug=F("channel_listings__channel__slug"))
        )

        shipping_methods_by_shipping_zone_and_channel_map = defaultdict(list)
        for shipping_method in shipping_methods:
            key = (
                shipping_method.shipping_zone_id,
                getattr(shipping_method, "channel_slug"),  # annotation
            )
            shipping_methods_by_shipping_zone_and_channel_map[key].append(
                shipping_method
            )
        return [
            shipping_methods_by_shipping_zone_and_channel_map.get(key, [])
            for key in keys
        ]


class ShippingMethodChannelListingByShippingMethodIdLoader(DataLoader):
    context_key = "shippingmethodchannellisting_by_shippingmethod"

    def batch_load(self, keys):
        shipping_method_channel_listings = ShippingMethodChannelListing.objects.using(
            self.database_connection_name
        ).filter(shipping_method_id__in=keys)
        shipping_method_channel_listings_by_shipping_method_map = defaultdict(list)
        for shipping_method_channel_listing in shipping_method_channel_listings:
            shipping_method_channel_listings_by_shipping_method_map[
                shipping_method_channel_listing.shipping_method_id
            ].append(shipping_method_channel_listing)
        return [
            shipping_method_channel_listings_by_shipping_method_map.get(
                shipping_method_id, []
            )
            for shipping_method_id in keys
        ]


class ShippingMethodChannelListingByChannelSlugLoader(DataLoader):
    context_key = "shippingmethodchannellisting_by_channel"

    def batch_load(self, keys):
        shipping_method_channel_listings = (
            ShippingMethodChannelListing.objects.using(self.database_connection_name)
            .filter(channel__slug__in=keys)
            .annotate(channel_slug=F("channel__slug"))
        )
        shipping_method_channel_listings_by_channel_slug = defaultdict(list)
        for shipping_method_channel_listing in shipping_method_channel_listings:
            shipping_method_channel_listings_by_channel_slug[
                shipping_method_channel_listing.channel_slug
            ].append(shipping_method_channel_listing)
        return [
            shipping_method_channel_listings_by_channel_slug.get(channel_slug, [])
            for channel_slug in keys
        ]


class ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(DataLoader):
    context_key = "shippingmethodchannellisting_by_shippingmethod_and_channel"

    def batch_load(self, keys):
        shipping_method_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]

        def _find_listing_by_shipping_method_id(listings_by_channel):
            listings_by_method = []
            for method_id, listings in zip(shipping_method_ids, listings_by_channel):
                for listing in listings:
                    if method_id == listing.shipping_method_id:
                        listings_by_method.append(listing)
                        break
                else:
                    listings_by_method.append(None)

            return listings_by_method

        return (
            ShippingMethodChannelListingByChannelSlugLoader(self.context)
            .load_many(channel_slugs)
            .then(_find_listing_by_shipping_method_id)
        )


class ChannelsByShippingZoneIdLoader(DataLoader):
    context_key = "channels_by_shippingzone"

    def batch_load(self, keys):
        from ..channel.dataloaders import ChannelByIdLoader

        channel_and_zone_is_pairs = (
            Channel.objects.using(self.database_connection_name)
            .filter(shipping_zones__id__in=keys)
            .values_list("pk", "shipping_zones__id")
        )
        shipping_zone_channel_map = defaultdict(list)
        for channel_id, zone_id in channel_and_zone_is_pairs:
            shipping_zone_channel_map[zone_id].append(channel_id)

        def map_channels(channels):
            channel_map = {channel.pk: channel for channel in channels}
            return [
                [
                    channel_map[channel_id]
                    for channel_id in shipping_zone_channel_map.get(zone_id, [])
                ]
                for zone_id in keys
            ]

        return (
            ChannelByIdLoader(self.context)
            .load_many({pk for pk, _ in channel_and_zone_is_pairs})
            .then(map_channels)
        )
