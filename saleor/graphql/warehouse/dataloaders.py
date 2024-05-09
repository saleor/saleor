import sys
from collections import defaultdict
from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Optional,
    TypedDict,
    Union,
)
from uuid import UUID

from django.contrib.sites.models import Site
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.db.models.aggregates import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django_stubs_ext import WithAnnotations
from promise import Promise

from ...channel.models import Channel
from ...product.models import ProductVariantChannelListing
from ...warehouse import WarehouseClickAndCollectOption
from ...warehouse.models import (
    ChannelWarehouse,
    PreorderReservation,
    Reservation,
    ShippingZone,
    Stock,
    Warehouse,
)
from ...warehouse.reservations import is_reservation_enabled
from ..channel.dataloaders import ChannelBySlugLoader
from ..core.dataloaders import DataLoader
from ..shipping.dataloaders import (
    ShippingZonesByChannelIdLoader,
    ShippingZonesByCountryLoader,
)
from ..site.dataloaders import get_site_promise

if TYPE_CHECKING:
    # https://github.com/typeddjango/django-stubs/issues/719

    class WithAvailableQuantity(TypedDict):
        available_quantity: int

    StockWithAvailableQuantity = WithAnnotations[Stock, WithAvailableQuantity]
else:
    StockWithAvailableQuantity = Stock


CountryCode = Optional[str]
VariantIdCountryCodeChannelSlug = tuple[int, CountryCode, str]


class AvailableQuantityByProductVariantIdCountryCodeAndChannelSlugLoader(
    DataLoader[VariantIdCountryCodeChannelSlug, int]
):
    """Calculates available variant quantity based on variant ID and country code.

    For each country code, for each shipping zone supporting that country,
    calculate the maximum available quantity, then return either that number
    or the maximum allowed checkout quantity, whichever is lower.
    """

    context_key = "available_quantity_by_productvariant_and_country"

    def batch_load(self, keys: Iterable[VariantIdCountryCodeChannelSlug]) -> list[int]:
        # Split the list of keys by country first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants,
        # so it's cheaper to execute one query per country.
        variants_by_country_and_channel: defaultdict[
            tuple[CountryCode, str], list[int]
        ] = defaultdict(list)
        for variant_id, country_code, channel_slug in keys:
            variants_by_country_and_channel[(country_code, channel_slug)].append(
                variant_id
            )

        # For each country code execute a single query for all product variants.
        quantity_by_variant_and_country: defaultdict[
            VariantIdCountryCodeChannelSlug, int
        ] = defaultdict(int)

        site = None
        if variants_by_country_and_channel:
            site = get_site_promise(self.context).get()
            for key, variant_ids in variants_by_country_and_channel.items():
                country_code, channel_slug = key
                quantities = self.batch_load_quantities_by_country(
                    country_code, channel_slug, variant_ids, site
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
        site: Site,
    ) -> Iterable[tuple[int, int]]:
        # get stocks only for warehouses assigned to the shipping zones
        # that are available in the given channel
        stocks = (
            Stock.objects.all()
            .using(self.database_connection_name)
            .filter(product_variant_id__in=variant_ids)
        )

        warehouse_shipping_zones = self.get_warehouse_shipping_zones(
            country_code, channel_slug
        )
        cc_warehouses = self.get_click_and_collect_warehouses(
            channel_slug, country_code
        )

        warehouse_shipping_zones_map = defaultdict(list)
        for warehouse_shipping_zone in warehouse_shipping_zones:
            warehouse_shipping_zones_map[warehouse_shipping_zone.warehouse_id].append(
                warehouse_shipping_zone.shippingzone_id
            )

        stocks = stocks.filter(
            Q(warehouse_id__in=warehouse_shipping_zones_map.keys())
            | Q(warehouse_id__in=cc_warehouses.values("id"))
        )

        stocks = stocks.annotate_available_quantity().order_by("pk")

        stocks_reservations = self.prepare_stocks_reservations_map(variant_ids)

        # A single country code (or a missing country code) can return results from
        # multiple shipping zones. We want to prepare warehouse by shipping zone map
        # and quantity by warehouse map. To be able to calculate max quantity available
        # in any shipping zones combination without duplicating warehouse quantity.
        (
            warehouse_ids_by_shipping_zone_by_variant,
            variants_with_global_cc_warehouses,
            available_quantity_by_warehouse_id_and_variant_id,
        ) = self.prepare_warehouse_ids_by_shipping_zone_and_variant_map(
            stocks, stocks_reservations, warehouse_shipping_zones_map, cc_warehouses
        )

        quantity_map = self.prepare_quantity_map(
            country_code,
            warehouse_ids_by_shipping_zone_by_variant,
            variants_with_global_cc_warehouses,
            available_quantity_by_warehouse_id_and_variant_id,
        )

        # Return the quantities after capping them at the maximum quantity allowed in
        # checkout. This prevent users from tracking the store's precise stock levels.
        global_quantity_limit = site.settings.limit_quantity_per_checkout
        return [
            (
                variant_id,
                min(quantity_map[variant_id], global_quantity_limit or sys.maxsize),
            )
            for variant_id in variant_ids
        ]

    def get_warehouse_shipping_zones(self, country_code, channel_slug):
        """Get the WarehouseShippingZone instances for a given channel and country."""
        WarehouseShippingZone = Warehouse.shipping_zones.through
        warehouse_shipping_zones = WarehouseShippingZone.objects.using(
            self.database_connection_name
        ).all()
        if country_code or channel_slug:
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
                ShippingZoneChannel = Channel.shipping_zones.through
                WarehouseChannel = Channel.warehouses.through
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
                warehouse_channels = (
                    WarehouseChannel.objects.using(self.database_connection_name)
                    .filter(
                        Exists(channels.filter(pk=OuterRef("channel_id"))),
                    )
                    .values("warehouse_id")
                )
                warehouse_shipping_zones = warehouse_shipping_zones.filter(
                    Exists(
                        shipping_zone_channels.filter(
                            shippingzone_id=OuterRef("shippingzone_id")
                        )
                    ),
                    Exists(
                        warehouse_channels.filter(warehouse_id=OuterRef("warehouse_id"))
                    ),
                )
        return warehouse_shipping_zones

    def get_click_and_collect_warehouses(self, channel_slug, country_code):
        """Get the collection point warehouses for a given channel and country code."""
        warehouses = Warehouse.objects.none()
        if not country_code and channel_slug:
            channels = (
                Channel.objects.using(self.database_connection_name)
                .filter(slug=channel_slug)
                .values("pk")
            )
            WarehouseChannel = Channel.warehouses.through
            warehouse_channels = (
                WarehouseChannel.objects.using(self.database_connection_name)
                .filter(
                    Exists(channels.filter(pk=OuterRef("channel_id"))),
                )
                .values("warehouse_id")
            )
            warehouses = Warehouse.objects.using(self.database_connection_name).filter(
                Exists(warehouse_channels.filter(warehouse_id=OuterRef("id"))),
                click_and_collect_option__in=[
                    WarehouseClickAndCollectOption.LOCAL_STOCK,
                    WarehouseClickAndCollectOption.ALL_WAREHOUSES,
                ],
            )
        return warehouses

    def prepare_stocks_reservations_map(self, variant_ids):
        """Prepare stock id to quantity reserved map for provided variant ids."""
        stocks_reservations = defaultdict(int)
        site = get_site_promise(self.context).get()
        if is_reservation_enabled(site.settings):
            # Can't do second annotation on same queryset because it made
            # available_quantity annotated value incorrect thanks to how
            # Django's ORM builds SQLs with annotations
            reservations_qs = (
                Stock.objects.using(self.database_connection_name)
                .filter(product_variant_id__in=variant_ids)
                .annotate_reserved_quantity()
                .order_by("pk")
                .values_list("id", "reserved_quantity")
            )
            for stock_id, quantity_reserved in reservations_qs:
                stocks_reservations[stock_id] = quantity_reserved
        return stocks_reservations

    def prepare_warehouse_ids_by_shipping_zone_and_variant_map(
        self,
        stocks: QuerySet[StockWithAvailableQuantity],
        stocks_reservations,
        warehouse_shipping_zones_map,
        cc_warehouses,
    ):
        """Combine all quantities within a single zone.

        Prepare `warehouse_ids_by_shipping_zone_by_variant` map in the following format:
            {
                variant_id: {
                    shipping_zone_id/warehouse_id: [
                        warehouse_id
                    ]
                }
            }

        In case of the collection point warehouses the warehouse_id is used instead of
        the shipping zone id. Every stock of the collection point warehouse is treated
        as a magic single-warehouse shipping zone.
        """
        cc_warehouses_in_bulk = cc_warehouses.in_bulk()
        warehouse_ids_by_shipping_zone_by_variant: defaultdict[
            int, defaultdict[Union[int, UUID], list[UUID]]
        ] = defaultdict(lambda: defaultdict(list))
        variants_with_global_cc_warehouses = []
        available_quantity_by_warehouse_id_and_variant_id: defaultdict[
            UUID, dict[int, int]
        ] = defaultdict(lambda: defaultdict(int))
        for stock in stocks:
            reserved_quantity = stocks_reservations[stock.id]
            quantity = stock.available_quantity - reserved_quantity
            # when the available_quantity was under 0 we do not want clipping to zero,
            # as it means that the stock might be exceeded
            if stock.available_quantity > 0:
                quantity = max(0, quantity)
            variant_id = stock.product_variant_id
            warehouse_id = stock.warehouse_id
            available_quantity_by_warehouse_id_and_variant_id[warehouse_id][
                variant_id
            ] += quantity
            if shipping_zone_ids := warehouse_shipping_zones_map[warehouse_id]:
                for shipping_zone_id in shipping_zone_ids:
                    warehouse_ids_by_shipping_zone_by_variant[variant_id][
                        shipping_zone_id
                    ].append(warehouse_id)
            else:
                cc_option = cc_warehouses_in_bulk[warehouse_id].click_and_collect_option
                # every stock of a collection point warehouse should treat as a magic
                # single-warehouse shipping zone
                warehouse_ids_by_shipping_zone_by_variant[variant_id][warehouse_id] = [
                    warehouse_id
                ]
                # in case of global warehouses the quantity available will be the sum
                # of the available quantity for that variant from all stocks,
                # so we need to keep information for which variant there is a warehouse
                # with the global stock
                if cc_option == WarehouseClickAndCollectOption.ALL_WAREHOUSES:
                    variants_with_global_cc_warehouses.append(variant_id)
        return (
            warehouse_ids_by_shipping_zone_by_variant,
            variants_with_global_cc_warehouses,
            available_quantity_by_warehouse_id_and_variant_id,
        )

    def prepare_quantity_map(
        self,
        country_code,
        warehouse_ids_by_shipping_zone_by_variant,
        variants_with_global_cc_warehouses,
        available_quantity_by_warehouse_id_and_variant_id,
    ):
        """Prepare the variant id to quantity map.

        When the country code is known, the available quantity is the sum of quantities
        from all shipping zones supporting given country. When the country is not known
        the highest known quantity is returned.

        The local warehouses are treated as a magic single-warehouse shipping zone.
        When the variant has any global collection point warehouse, the quantity is the
        sum of the quantities from all shipping zones.
        In case of global warehouses the available quantity of such collection point
        is the sum of the available quantities from all stocks that passed the country
        or channel conditions.
        """
        quantity_map: defaultdict[int, int] = defaultdict(int)
        for (
            variant_id,
            warehouse_ids_shipping_zone,
        ) in warehouse_ids_by_shipping_zone_by_variant.items():
            if country_code or variant_id in variants_with_global_cc_warehouses:
                used_warehouse_ids = []
                for warehouse_ids in warehouse_ids_shipping_zone.values():
                    used_warehouse_ids.extend(warehouse_ids)
                used_warehouse_ids = set(used_warehouse_ids)
                # When country code is known or the global collection point warehouse
                # for this variant exists, return the sum of quantities from all
                # shipping zones supporting given country.
                quantity = 0
                for warehouse_id in used_warehouse_ids:
                    quantity += available_quantity_by_warehouse_id_and_variant_id[
                        warehouse_id
                    ][variant_id]
                quantity_map[variant_id] = quantity
            else:
                # When country code is unknown, return the highest known quantity.
                quantity_values = []
                for (
                    warehouse_ids_per_shipping_zones
                ) in warehouse_ids_shipping_zone.values():
                    quantity = 0
                    for warehouse_id in warehouse_ids_per_shipping_zones:
                        quantity += available_quantity_by_warehouse_id_and_variant_id[
                            warehouse_id
                        ][variant_id]
                    quantity_values.append(quantity)

                quantity_map[variant_id] = max(quantity_values)

        return quantity_map


class StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader(
    DataLoader[VariantIdCountryCodeChannelSlug, Iterable[Stock]]
):
    """Return stocks with available quantity based on variant ID, country code, channel.

    For each country code, for each shipping zone supporting that country and channel,
    return stocks with maximum available quantity.
    """

    context_key = "stocks_with_available_quantity_by_productvariant_country_and_channel"

    def batch_load(self, keys):
        def with_channels(channels):
            def with_shipping_zones(data):
                def with_warehouses(warehouse_data):
                    warehouses_by_channel, warehouses_by_zone = warehouse_data

                    # build maps
                    variant_ids_by_country_and_channel_map: defaultdict[
                        tuple[CountryCode, str], list[int]
                    ] = defaultdict(list)
                    for variant_id, country_code, channel_slug in keys:
                        variant_ids_by_country_and_channel_map[
                            (country_code, channel_slug)
                        ].append(variant_id)

                    shipping_zones_by_channel_map = {
                        channel.slug: set(shipping_zones)
                        for shipping_zones, channel in zip(
                            shipping_zones_by_channel, channels
                        )
                    }
                    shipping_zones_by_country_map = {
                        country_code: set(shipping_zones)
                        for shipping_zones, country_code in zip(
                            shipping_zones_by_country, country_codes
                        )
                    }
                    warehouses_by_channel_map = {
                        channel.slug: set(warehouses)
                        for warehouses, channel in zip(warehouses_by_channel, channels)
                    }
                    warehouses_by_zone_map = {
                        shipping_zone_id: set(warehouses)
                        for warehouses, shipping_zone_id in zip(
                            warehouses_by_zone, shipping_zone_ids
                        )
                    }

                    # filter warehouses
                    warehouse_ids_by_country_and_channel_map = (
                        self.get_relevant_warehouses(
                            variant_ids_by_country_and_channel_map,
                            shipping_zones_by_channel_map,
                            shipping_zones_by_country_map,
                            warehouses_by_channel_map,
                            warehouses_by_zone_map,
                        )
                    )

                    variant_ids = list(set(key[0] for key in keys))
                    warehouse_ids = {
                        warehouse_id
                        for warehouse_ids in warehouse_ids_by_country_and_channel_map.values()  # noqa: E501
                        for warehouse_id in warehouse_ids
                    }
                    stocks_qs = Stock.objects.using(
                        self.database_connection_name
                    ).filter(
                        product_variant_id__in=variant_ids,
                        warehouse_id__in=warehouse_ids,
                    )

                    stocks_qs = stocks_qs.annotate_available_quantity().order_by("pk")

                    results = []
                    for variant_id, country_code, channel_slug in keys:
                        warehouse_ids = warehouse_ids_by_country_and_channel_map[
                            (country_code, channel_slug)
                        ]
                        stocks = [
                            stock
                            for stock in stocks_qs
                            if stock.product_variant_id == variant_id
                            and stock.warehouse_id in warehouse_ids
                        ]
                        results.append(stocks)

                    return results

                shipping_zones_by_channel, shipping_zones_by_country = data
                channel_ids = [channel.id for channel in channels]

                shipping_zone_by_channel_ids = {
                    shipping_zone.id
                    for shipping_zones in shipping_zones_by_channel
                    for shipping_zone in shipping_zones
                }
                shipping_zone_by_country_ids = {
                    shipping_zone.id
                    for shipping_zones in shipping_zones_by_country
                    for shipping_zone in shipping_zones
                }
                shipping_zone_ids = (
                    shipping_zone_by_channel_ids | shipping_zone_by_country_ids
                )

                warehouses_by_channel = WarehousesByChannelIdLoader(
                    self.context
                ).load_many(channel_ids)
                warehouses_by_zone = WarehousesByShippingZoneIdLoader(
                    self.context
                ).load_many(shipping_zone_ids)
                return Promise.all([warehouses_by_channel, warehouses_by_zone]).then(
                    with_warehouses
                )

            channel_ids = [channel.id for channel in set(channels)]
            shipping_zones_by_channel = ShippingZonesByChannelIdLoader(
                self.context
            ).load_many(channel_ids)

            country_codes = list(set(key[1] for key in keys if key[1]))
            shipping_zones_by_country = ShippingZonesByCountryLoader(
                self.context
            ).load_many(country_codes)

            return Promise.all(
                [shipping_zones_by_channel, shipping_zones_by_country]
            ).then(with_shipping_zones)

        channel_slugs = list(set(key[2] for key in keys if key[2]))
        return (
            ChannelBySlugLoader(self.context)
            .load_many(channel_slugs)
            .then(with_channels)
        )

    @staticmethod
    def get_relevant_warehouses(
        variant_ids_by_country_and_channel_map,
        shipping_zones_by_channel_map,
        shipping_zones_by_country_map,
        warehouses_by_channel_map,
        warehouses_by_zone_map,
    ):
        warehouse_ids_by_country_and_channel_map = defaultdict(list)
        for (
            country_code,
            channel_slug,
        ), variant_ids in variant_ids_by_country_and_channel_map.items():
            warehouses = set()
            warehouses_in_country = set()
            # get warehouses from shipping zones in specific country
            if country_code:
                shipping_zones_in_country = shipping_zones_by_country_map[country_code]
                for zone in shipping_zones_in_country:
                    warehouses_in_country |= warehouses_by_zone_map[zone.id]

            if channel_slug:
                warehouses_in_channel = warehouses_by_channel_map[channel_slug]
                shipping_zones_in_channel = shipping_zones_by_channel_map[channel_slug]
                cc_options = [
                    WarehouseClickAndCollectOption.LOCAL_STOCK,
                    WarehouseClickAndCollectOption.ALL_WAREHOUSES,
                ]
                # get click & collect warehouses available in channel
                cc_warehouses_in_channel = {
                    warehouse
                    for warehouse in warehouses_in_channel
                    if warehouse.click_and_collect_option in cc_options
                }

                # get warehouses with shipping zone, both available in channel
                warehouses_with_zone_in_channel = set()
                for zone in shipping_zones_in_channel:
                    warehouses_with_zone_in_channel |= (
                        warehouses_by_zone_map[zone.id] & warehouses_in_channel
                    )

                warehouses = cc_warehouses_in_channel | warehouses_with_zone_in_channel
                if country_code:
                    warehouses &= warehouses_in_country

            warehouse_ids_by_country_and_channel_map[(country_code, channel_slug)] = [
                warehouse.id for warehouse in warehouses
            ]

        return warehouse_ids_by_country_and_channel_map


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
        )
        for reservation in queryset:
            reservations_by_checkout_line[reservation.checkout_line_id].append(
                reservation
            )
        queryset = (
            PreorderReservation.objects.using(self.database_connection_name)
            .filter(checkout_line_id__in=keys)
            .not_expired()
        )
        for reservation in queryset:
            reservations_by_checkout_line[reservation.checkout_line_id].append(
                reservation
            )
        return [reservations_by_checkout_line[key] for key in keys]


class PreorderQuantityReservedByVariantChannelListingIdLoader(DataLoader[int, int]):
    context_key = "preorder_quantity_reserved_by_variant_channel_listing_id"

    def batch_load(self, keys: Iterable[int]):
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
            .order_by("pk")
            .values("id", "quantity_reserved")
        )

        reservations_by_listing_id: defaultdict[int, int] = defaultdict(int)
        for listing in queryset:
            reservations_by_listing_id[listing["id"]] += listing["quantity_reserved"]
        return [reservations_by_listing_id[key] for key in keys]


class WarehouseByIdLoader(DataLoader):
    context_key = "warehouse_by_id"

    def batch_load(self, keys: Iterable[UUID]) -> list[Optional[Warehouse]]:
        warehouses = (
            Warehouse.objects.all().using(self.database_connection_name).in_bulk(keys)
        )
        return [warehouses.get(warehouse_uuid) for warehouse_uuid in keys]


class StockByIdLoader(DataLoader):
    context_key = "stock_by_id"

    def batch_load(self, keys):
        stocks = Stock.objects.using(self.database_connection_name).in_bulk(keys)
        return [stocks.get(key) for key in keys]


class StocksByWarehouseIdLoader(DataLoader):
    context_key = "stocks_by_warehouse"

    def batch_load(self, keys):
        stocks = Stock.objects.using(self.database_connection_name).filter(
            warehouse_id__in=keys
        )
        stocks_map = defaultdict(list)
        for stock in stocks:
            stocks_map[stock.warehouse_id].append(stock)
        return [stocks_map.get(warehouse_id, []) for warehouse_id in keys]


class WarehousesByChannelIdLoader(DataLoader):
    context_key = "warehouse_by_channel"

    def batch_load(self, keys):
        warehouse_and_channel_in_pairs = (
            ChannelWarehouse.objects.using(self.database_connection_name)
            .filter(channel_id__in=keys)
            .values_list("warehouse_id", "channel_id")
        )
        channel_warehouse_map = defaultdict(list)
        for warehouse_id, channel_id in warehouse_and_channel_in_pairs:
            channel_warehouse_map[channel_id].append(warehouse_id)

        def map_warehouses(warehouses):
            warehouse_map = {warehouse.pk: warehouse for warehouse in warehouses}
            return [
                [
                    warehouse_map[warehouse_id]
                    for warehouse_id in channel_warehouse_map[channel_id]
                ]
                for channel_id in keys
            ]

        return (
            WarehouseByIdLoader(self.context)
            .load_many({pk for pk, _ in warehouse_and_channel_in_pairs})
            .then(map_warehouses)
        )


class WarehousesByShippingZoneIdLoader(DataLoader):
    context_key = "warehouses_by_shipping_zone_id"

    def batch_load(self, keys):
        warehouse_and_shipping_zone_in_pairs = (
            ShippingZone.warehouses.through.objects.using(self.database_connection_name)
            .filter(shippingzone_id__in=keys)
            .values_list("warehouse_id", "shippingzone_id")
        )

        shipping_zone_warehouse_map = defaultdict(list)
        for warehouse_id, shipping_zone_id in warehouse_and_shipping_zone_in_pairs:
            shipping_zone_warehouse_map[shipping_zone_id].append(warehouse_id)

        def map_warehouses(warehouses):
            warehouse_map = {warehouse.pk: warehouse for warehouse in warehouses}
            return [
                [
                    warehouse_map[warehouse_id]
                    for warehouse_id in shipping_zone_warehouse_map[shipping_zone_id]
                ]
                for shipping_zone_id in keys
            ]

        return (
            WarehouseByIdLoader(self.context)
            .load_many({pk for pk, _ in warehouse_and_shipping_zone_in_pairs})
            .then(map_warehouses)
        )


class StocksByProductVariantIdLoader(DataLoader):
    context_key = "stocks_by_product_variant"

    def batch_load(self, keys):
        stocks = Stock.objects.using(self.database_connection_name).filter(
            product_variant_id__in=keys
        )
        stocks_by_variant_id = defaultdict(list)
        for stock in stocks:
            stocks_by_variant_id[stock.product_variant_id].append(stock)

        return [stocks_by_variant_id[key] for key in keys]
