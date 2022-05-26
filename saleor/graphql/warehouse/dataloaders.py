import sys
from collections import defaultdict
from typing import DefaultDict, Iterable, List, Optional, Tuple
from uuid import UUID

from django.db.models import Exists, OuterRef, Q
from django.db.models.aggregates import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from ...channel.models import Channel
from ...product.models import ProductVariantChannelListing
from ...warehouse.models import (
    PreorderReservation,
    Reservation,
    ShippingZone,
    Stock,
    Warehouse,
)
from ...warehouse.reservations import is_reservation_enabled
from ..core.dataloaders import DataLoader

CountryCode = Optional[str]
VariantIdCountryCodeChannelSlug = Tuple[int, CountryCode, str]


class AvailableQuantityByProductVariantIdCountryCodeAndChannelSlugLoader(
    DataLoader[VariantIdCountryCodeChannelSlug, int]
):
    """Calculates available variant quantity based on variant ID and country code.

    For each country code, for each shipping zone supporting that country,
    calculate the maximum available quantity, then return either that number
    or the maximum allowed checkout quantity, whichever is lower.
    """

    context_key = "available_quantity_by_productvariant_and_country"

    def batch_load(self, keys):
        # Split the list of keys by country first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants
        # so it's cheaper to execute one query per country.
        variants_by_country_and_channel: DefaultDict[
            Tuple[CountryCode, str], List[int]
        ] = defaultdict(list)
        for variant_id, country_code, channel_slug in keys:
            variants_by_country_and_channel[(country_code, channel_slug)].append(
                variant_id
            )

        # For each country code execute a single query for all product variants.
        quantity_by_variant_and_country: DefaultDict[
            VariantIdCountryCodeChannelSlug, int
        ] = defaultdict(int)
        for key, variant_ids in variants_by_country_and_channel.items():
            country_code, channel_slug = key
            quantities = self.batch_load_quantities_by_country(
                country_code, channel_slug, variant_ids
            )
            for variant_id, quantity in quantities:
                quantity_by_variant_and_country[
                    (variant_id, country_code, channel_slug)
                ] = max(0, quantity)

        return [quantity_by_variant_and_country[key] for key in keys]

    def batch_load_quantities_by_country(
        self,
        country_code: Optional[CountryCode],
        channel_slug: Optional[str],
        variant_ids: Iterable[int],
    ) -> Iterable[Tuple[int, int]]:
        # get stocks only for warehouses assigned to the shipping zones
        # that are available in the given channel
        stocks = Stock.objects.using(self.database_connection_name).filter(
            product_variant_id__in=variant_ids
        )
        WarehouseShippingZone = Warehouse.shipping_zones.through  # type: ignore
        warehouse_shipping_zones = WarehouseShippingZone.objects.using(
            self.database_connection_name
        ).all()
        additional_warehouse_filter = False
        if country_code or channel_slug:
            additional_warehouse_filter = True
            if country_code:
                shipping_zones = (
                    ShippingZone.objects.using(self.database_connection_name)
                    .filter(countries__contains=country_code)
                    .values("pk")
                )
                warehouse_shipping_zones = warehouse_shipping_zones.filter(
                    Exists(shipping_zones.filter(pk=OuterRef("shippingzone_id")))
                )
            if channel_slug:
                ShippingZoneChannel = Channel.shipping_zones.through  # type: ignore
                channels = (
                    Channel.objects.using(self.database_connection_name)
                    .filter(slug=channel_slug)
                    .values("pk")
                )
                shipping_zone_channels = (
                    ShippingZoneChannel.objects.using(self.database_connection_name)
                    .filter(Exists(channels.filter(pk=OuterRef("channel_id"))))
                    .values("shippingzone_id")
                )
                warehouse_shipping_zones = warehouse_shipping_zones.filter(
                    Exists(
                        shipping_zone_channels.filter(
                            shippingzone_id=OuterRef("shippingzone_id")
                        )
                    )
                )
        warehouse_shipping_zones_map = defaultdict(list)
        for warehouse_shipping_zone in warehouse_shipping_zones:
            warehouse_shipping_zones_map[warehouse_shipping_zone.warehouse_id].append(
                warehouse_shipping_zone.shippingzone_id
            )
        if additional_warehouse_filter:
            stocks = stocks.filter(warehouse_id__in=warehouse_shipping_zones_map.keys())
        stocks = stocks.annotate_available_quantity()

        stocks_reservations = defaultdict(int)
        if is_reservation_enabled(self.context.site.settings):  # type: ignore
            # Can't do second annotation on same queryset because it made
            # available_quantity annotated value incorrect thanks to how
            # Django's ORM builds SQLs with annotations
            reservations_qs = (
                Stock.objects.using(self.database_connection_name)
                .filter(product_variant_id__in=variant_ids)
                .annotate_reserved_quantity()
                .values_list("id", "reserved_quantity")
            )
            for stock_id, quantity_reserved in reservations_qs:
                stocks_reservations[stock_id] = quantity_reserved

        # A single country code (or a missing country code) can return results from
        # multiple shipping zones. We want to combine all quantities within a single
        # zone and then find out which zone contains the highest total.
        quantity_by_shipping_zone_by_product_variant: DefaultDict[
            int, DefaultDict[int, int]
        ] = defaultdict(lambda: defaultdict(int))
        for stock in stocks:
            reserved_quantity = stocks_reservations[stock.id]
            quantity = max(0, stock.available_quantity - reserved_quantity)
            variant_id = stock.product_variant_id
            warehouse_id = stock.warehouse_id
            shipping_zone_ids = warehouse_shipping_zones_map[warehouse_id]
            for shipping_zone_id in shipping_zone_ids:
                quantity_by_shipping_zone_by_product_variant[variant_id][
                    shipping_zone_id
                ] += quantity

        quantity_map: DefaultDict[int, int] = defaultdict(int)
        for (
            variant_id,
            quantity_by_shipping_zone,
        ) in quantity_by_shipping_zone_by_product_variant.items():
            quantity_values = quantity_by_shipping_zone.values()
            if country_code:
                # When country code is known, return the sum of quantities from all
                # shipping zones supporting given country.
                quantity_map[variant_id] = sum(quantity_values)
            else:
                # When country code is unknown, return the highest known quantity.
                quantity_map[variant_id] = max(quantity_values)

        # Return the quantities after capping them at the maximum quantity allowed in
        # checkout. This prevent users from tracking the store's precise stock levels.
        global_quantity_limit = (
            self.context.site.settings.limit_quantity_per_checkout  # type: ignore
        )
        return [
            (
                variant_id,
                min(quantity_map[variant_id], global_quantity_limit or sys.maxsize),
            )
            for variant_id in variant_ids
        ]


class StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader(
    DataLoader[VariantIdCountryCodeChannelSlug, Iterable[Stock]]
):
    """Return stocks with available quantity based on variant ID, country code, channel.

    For each country code, for each shipping zone supporting that country and channel,
    return stocks with maximum available quantity.
    """

    context_key = "stocks_with_available_quantity_by_productvariant_country_and_channel"

    def batch_load(self, keys):
        # Split the list of keys by country first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants
        # so it's cheaper to execute one query per country.
        variants_by_country_and_channel: DefaultDict[
            CountryCode, List[int]
        ] = defaultdict(list)
        for variant_id, country_code, channel_slug in keys:
            variants_by_country_and_channel[(country_code, channel_slug)].append(
                variant_id
            )

        # For each country code execute a single query for all product variants.
        stocks_by_variant_and_country: DefaultDict[
            VariantIdCountryCodeChannelSlug, Iterable[Stock]
        ] = defaultdict(list)
        for key, variant_ids in variants_by_country_and_channel.items():
            country_code, channel_slug = key
            variant_ids_stocks = self.batch_load_stocks_by_country(
                country_code, channel_slug, variant_ids
            )
            for variant_id, stocks in variant_ids_stocks:
                stocks_by_variant_and_country[
                    (variant_id, country_code, channel_slug)
                ].extend(stocks)

        return [stocks_by_variant_and_country[key] for key in keys]

    def batch_load_stocks_by_country(
        self,
        country_code: Optional[CountryCode],
        channel_slug: Optional[str],
        variant_ids: Iterable[int],
    ) -> Iterable[Tuple[int, List[Stock]]]:
        stocks = Stock.objects.using(self.database_connection_name).filter(
            product_variant_id__in=variant_ids
        )
        if country_code:
            stocks = stocks.filter(
                warehouse__shipping_zones__countries__contains=country_code
            )
        if channel_slug:
            stocks = stocks.filter(
                warehouse__shipping_zones__channels__slug=channel_slug
            )
        stocks = stocks.annotate_available_quantity()

        stocks_by_variant_id_map: DefaultDict[int, List[Stock]] = defaultdict(list)
        for stock in stocks:
            stocks_by_variant_id_map[stock.product_variant_id].append(stock)

        return [
            (
                variant_id,
                stocks_by_variant_id_map[variant_id],
            )
            for variant_id in variant_ids
        ]


class StocksReservationsByCheckoutTokenLoader(DataLoader):
    context_key = "stock_reservations_by_checkout_token"

    def batch_load(self, keys):
        from ..checkout.dataloaders import CheckoutLinesByCheckoutTokenLoader

        def with_checkouts_lines(checkouts_lines):
            checkouts_keys_map = {}
            for i, key in enumerate(keys):
                for checkout_line in checkouts_lines[i]:
                    checkouts_keys_map[checkout_line.id] = key

            def with_lines_reservations(lines_reservations):
                reservations_map = defaultdict(list)
                for reservations in lines_reservations:
                    for reservation in reservations:
                        checkout_key = checkouts_keys_map[reservation.checkout_line_id]
                        reservations_map[checkout_key].append(reservation)

                return [reservations_map[key] for key in keys]

            return (
                ActiveReservationsByCheckoutLineIdLoader(self.context)
                .load_many(checkouts_keys_map.keys())
                .then(with_lines_reservations)
            )

        return (
            CheckoutLinesByCheckoutTokenLoader(self.context)
            .load_many(keys)
            .then(with_checkouts_lines)
        )


class ActiveReservationsByCheckoutLineIdLoader(DataLoader):
    context_key = "active_reservations_by_checkout_line_id"

    def batch_load(self, keys):
        reservations_by_checkout_line = defaultdict(list)
        queryset = (
            Reservation.objects.using(self.database_connection_name)
            .filter(checkout_line_id__in=keys)
            .not_expired()
        )  # type: ignore
        for reservation in queryset:
            reservations_by_checkout_line[reservation.checkout_line_id].append(
                reservation
            )
        queryset = (
            PreorderReservation.objects.using(self.database_connection_name)
            .filter(checkout_line_id__in=keys)
            .not_expired()
        )  # type: ignore
        for reservation in queryset:
            reservations_by_checkout_line[reservation.checkout_line_id].append(
                reservation
            )
        return [reservations_by_checkout_line[key] for key in keys]


class PreorderQuantityReservedByVariantChannelListingIdLoader(DataLoader):
    context_key = "preorder_quantity_reserved_by_variant_channel_listing_id"

    def batch_load(self, keys):
        queryset = (
            ProductVariantChannelListing.objects.using(self.database_connection_name)
            .filter(id__in=keys)
            .annotate(
                quantity_reserved=Coalesce(
                    Sum("preorder_reservations__quantity_reserved"),
                    0,
                ),
                where=Q(preorder_reservations__reserved_until__gt=timezone.now()),
            )
            .values("id", "quantity_reserved")
        )

        reservations_by_listing_id = defaultdict(int)
        for listing in queryset:
            reservations_by_listing_id[listing["id"]] += listing["quantity_reserved"]
        return [reservations_by_listing_id[key] for key in keys]


class WarehouseByIdLoader(DataLoader):
    context_key = "warehouse_by_id"

    def batch_load(self, keys: Iterable[UUID]) -> List[Optional[Warehouse]]:
        warehouses = Warehouse.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [warehouses.get(warehouse_uuid) for warehouse_uuid in keys]


class StockByIdLoader(DataLoader):
    context_key = "stock_by_id"

    def batch_load(self, keys):
        return Stock.objects.using(self.database_connection_name).in_bulk(keys).values()
