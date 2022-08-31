import itertools
import uuid
from typing import Iterable, Optional, Set

from django.db import models
from django.db.models import Count, Exists, F, OuterRef, Prefetch, Q, Sum
from django.db.models.expressions import Subquery
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.utils import timezone

from ..account.models import Address
from ..channel.models import Channel
from ..checkout.models import CheckoutLine
from ..core.models import ModelWithMetadata, SortableModel
from ..order.models import OrderLine
from ..product.models import Product, ProductVariant, ProductVariantChannelListing
from ..shipping.models import ShippingZone
from . import WarehouseClickAndCollectOption


class WarehouseQueryset(models.QuerySet):
    def for_channel(self, channel_id: int):
        WarehouseChannel = Channel.warehouses.through  # type: ignore
        return self.filter(
            Exists(
                WarehouseChannel.objects.filter(
                    channel_id=channel_id, warehouse_id=OuterRef("id")
                )
            )
        ).order_by("pk")

    def for_country_and_channel(self, country: str, channel_id: int):
        ShippingZoneChannel = Channel.shipping_zones.through  # type: ignore
        WarehouseShippingZone = ShippingZone.warehouses.through  # type: ignore
        WarehouseChannel = Channel.warehouses.through  # type: ignore

        shipping_zones = ShippingZone.objects.filter(
            countries__contains=country
        ).values("pk")
        shipping_zone_channels = ShippingZoneChannel.objects.filter(
            Exists(shipping_zones.filter(pk=OuterRef("shippingzone_id"))),
            channel_id=channel_id,
        )

        warehouse_shipping_zones = WarehouseShippingZone.objects.filter(
            Exists(
                shipping_zone_channels.filter(
                    shippingzone_id=OuterRef("shippingzone_id")
                )
            ),
            Exists(
                WarehouseChannel.objects.filter(
                    channel_id=channel_id, warehouse_id=OuterRef("warehouse_id")
                )
            ),
        ).values("warehouse_id")
        return self.filter(
            Exists(warehouse_shipping_zones.filter(warehouse_id=OuterRef("pk")))
        ).order_by("pk")

    def applicable_for_click_and_collect_no_quantity_check(
        self, lines_qs: QuerySet[CheckoutLine], channel_id: int
    ):
        """Return the queryset of a `Warehouse` which are applicable for click and collect.

        Note this method does not check stocks quantity for given `CheckoutLine`s.
        This method should be used only if stocks quantity will be checked in further
        validation steps, for instance in checkout completion.
        """
        if all(
            line.variant.is_preorder_active()
            for line in lines_qs.select_related("variant").only("variant_id")
        ):
            return self._for_channel_click_and_collect(channel_id)

        stocks_qs = Stock.objects.filter(
            product_variant__id__in=lines_qs.values("variant_id"),
        ).select_related("product_variant")

        return self._for_channel_lines_and_stocks(lines_qs, stocks_qs, channel_id)

    def applicable_for_click_and_collect(
        self, lines_qs: QuerySet[CheckoutLine], channel_id: int
    ) -> QuerySet["Warehouse"]:
        """Return the queryset of a `Warehouse` which are applicable for click and collect.

        Note additional check of stocks quantity for given `CheckoutLine`s.
        For `WarehouseClickAndCollect.LOCAL` all `CheckoutLine`s must be available from
        a single warehouse.
        """

        if all(
            line.variant.is_preorder_active()
            for line in lines_qs.select_related("variant").only("variant_id")
        ):
            return self._for_channel_click_and_collect(channel_id)

        lines_quantity = (
            lines_qs.filter(variant_id=OuterRef("product_variant_id"))
            .annotate(prod_sum=Sum("quantity"))
            .values_list("prod_sum")
        )

        stocks_qs = (
            Stock.objects.annotate_available_quantity()
            .annotate(line_quantity=F("available_quantity") - Subquery(lines_quantity))
            .order_by("line_quantity")
            .filter(
                product_variant__id__in=lines_qs.values("variant_id"),
                line_quantity__gte=0,
            )
            .select_related("product_variant")
        )

        return self._for_channel_lines_and_stocks(lines_qs, stocks_qs, channel_id)

    def _for_channel_lines_and_stocks(
        self,
        lines_qs: QuerySet[CheckoutLine],
        stocks_qs: QuerySet["Stock"],
        channel_id: int,
    ) -> QuerySet["Warehouse"]:
        warehouse_cc_option_enum = WarehouseClickAndCollectOption

        return (
            self.for_channel(channel_id)
            .prefetch_related(Prefetch("stock_set", queryset=stocks_qs))
            .filter(stock__in=stocks_qs)
            .annotate(stock_num=Count("stock__id", distinct=True))
            .filter(
                Q(stock_num=lines_qs.count())
                & Q(click_and_collect_option=warehouse_cc_option_enum.LOCAL_STOCK)
                | Q(click_and_collect_option=warehouse_cc_option_enum.ALL_WAREHOUSES)
            )
        )

    def _for_channel_click_and_collect(self, channel_id: int) -> QuerySet["Warehouse"]:
        return self.for_channel(channel_id).filter(
            click_and_collect_option__in=[
                WarehouseClickAndCollectOption.LOCAL_STOCK,
                WarehouseClickAndCollectOption.ALL_WAREHOUSES,
            ]
        )


class ChannelWarehouse(SortableModel):
    channel = models.ForeignKey(
        Channel, related_name="channelwarehouse", on_delete=models.CASCADE
    )
    warehouse = models.ForeignKey(
        "Warehouse", related_name="channelwarehouse", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("channel", "warehouse"),)
        ordering = ("sort_order", "pk")

    def get_ordering_queryset(self):
        return self.channel.channelwarehouse.all()


class Warehouse(ModelWithMetadata):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    channels = models.ManyToManyField(
        Channel, related_name="warehouses", through=ChannelWarehouse
    )
    shipping_zones = models.ManyToManyField(
        ShippingZone, blank=True, related_name="warehouses"
    )
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    email = models.EmailField(blank=True, default="")
    click_and_collect_option = models.CharField(
        max_length=30,
        choices=WarehouseClickAndCollectOption.CHOICES,
        default=WarehouseClickAndCollectOption.DISABLED,
    )
    is_private = models.BooleanField(default=True)

    objects = models.Manager.from_queryset(WarehouseQueryset)()

    class Meta(ModelWithMetadata.Meta):
        ordering = ("-slug",)

    def __str__(self):
        return self.name

    @property
    def countries(self) -> Set[str]:
        shipping_zones = self.shipping_zones.all()
        return set(itertools.chain(*[zone.countries for zone in shipping_zones]))

    def delete(self, *args, **kwargs):
        address = self.address
        super().delete(*args, **kwargs)
        address.delete()


class StockQuerySet(models.QuerySet):
    def annotate_available_quantity(self):
        return self.annotate(
            available_quantity=F("quantity")
            - Coalesce(
                Sum(
                    "allocations__quantity_allocated",
                    filter=Q(allocations__quantity_allocated__gt=0),
                ),
                0,
            )
        )

    def annotate_reserved_quantity(self):
        return self.annotate(
            reserved_quantity=Coalesce(
                Sum(
                    "reservations__quantity_reserved",
                    filter=Q(reservations__reserved_until__gt=timezone.now()),
                ),
                0,
            )
        )

    def for_channel_and_click_and_collect(self, channel_slug: str):
        """Return the stocks for a given channel for a click and collect.

        The click and collect warehouses don't have to be assigned to the shipping zones
        so all stocks for a given channel are returned.
        """
        WarehouseChannel = Channel.warehouses.through  # type: ignore

        channels = Channel.objects.filter(slug=channel_slug).values("pk")

        warehouse_channels = WarehouseChannel.objects.filter(
            Exists(channels.filter(pk=OuterRef("channel_id")))
        ).values("warehouse_id")

        return self.select_related("product_variant").filter(
            Exists(warehouse_channels.filter(warehouse_id=OuterRef("warehouse_id")))
        )

    def for_channel_and_country(
        self,
        channel_slug: str,
        country_code: Optional[str] = None,
        include_cc_warehouses: bool = False,
    ):
        """Get stocks for given channel and country_code.

        The returned stocks, must be in warehouse that is available in provided channel
        and in the shipping zone that is available in the given channel and country.
        When the country_code is not provided or include_cc_warehouses is set to True,
        also the stocks from collection point warehouses allowed in given channel are
        returned.
        """
        ShippingZoneChannel = Channel.shipping_zones.through  # type: ignore
        WarehouseShippingZone = ShippingZone.warehouses.through  # type: ignore
        WarehouseChannel = Channel.warehouses.through  # type: ignore

        channels = Channel.objects.filter(slug=channel_slug).values("pk")

        shipping_zone_channels = ShippingZoneChannel.objects.filter(
            Exists(channels.filter(pk=OuterRef("channel_id")))
        )
        warehouse_channels = WarehouseChannel.objects.filter(
            Exists(channels.filter(pk=OuterRef("channel_id")))
        ).values("warehouse_id")

        cc_warehouses = Warehouse.objects.none()
        if country_code:
            shipping_zones = ShippingZone.objects.filter(
                countries__contains=country_code
            ).values("pk")
            shipping_zone_channels = shipping_zone_channels.filter(
                Exists(shipping_zones.filter(pk=OuterRef("shippingzone_id")))
            )
        if not country_code or include_cc_warehouses:
            # when the country code is not provided we should also include
            # the collection point warehouses
            cc_warehouses = Warehouse.objects.filter(
                Exists(warehouse_channels.filter(warehouse_id=OuterRef("id"))),
                click_and_collect_option__in=[
                    WarehouseClickAndCollectOption.LOCAL_STOCK,
                    WarehouseClickAndCollectOption.ALL_WAREHOUSES,
                ],
            )

        shipping_zone_channels.values("shippingzone_id")

        warehouse_shipping_zones = WarehouseShippingZone.objects.filter(
            Exists(
                shipping_zone_channels.filter(
                    shippingzone_id=OuterRef("shippingzone_id")
                )
            ),
            Exists(warehouse_channels.filter(warehouse_id=OuterRef("warehouse_id"))),
        ).values("warehouse_id")
        return self.select_related("product_variant").filter(
            Exists(
                warehouse_shipping_zones.filter(warehouse_id=OuterRef("warehouse_id"))
            )
            | Exists(cc_warehouses.filter(id=OuterRef("warehouse_id")))
        )

    def get_variant_stocks_for_country(
        self, country_code: str, channel_slug: str, product_variant: ProductVariant
    ):
        """Return the stock information about the a stock for a given country.

        Note it will raise a 'Stock.DoesNotExist' exception if no such stock is found.
        """
        return self.for_channel_and_country(channel_slug, country_code).filter(
            product_variant=product_variant
        )

    def get_variants_stocks_for_country(
        self,
        country_code: str,
        channel_slug: str,
        products_variants: Iterable[ProductVariant],
    ):
        """Return the stock information about the a stock for a given country.

        Note it will raise a 'Stock.DoesNotExist' exception if no such stock is found.
        """
        return self.for_channel_and_country(channel_slug, country_code).filter(
            product_variant__in=products_variants
        )

    def get_product_stocks_for_country_and_channel(
        self, country_code: str, channel_slug: str, product: Product
    ):
        return self.for_channel_and_country(channel_slug, country_code).filter(
            product_variant__product_id=product.pk
        )


class Stock(models.Model):
    warehouse = models.ForeignKey(Warehouse, null=False, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        ProductVariant, null=False, on_delete=models.CASCADE, related_name="stocks"
    )
    quantity = models.IntegerField(default=0)
    quantity_allocated = models.IntegerField(default=0)

    objects = models.Manager.from_queryset(StockQuerySet)()

    class Meta:
        unique_together = [["warehouse", "product_variant"]]
        ordering = ("pk",)

    def increase_stock(self, quantity: int, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.quantity = F("quantity") + quantity
        if commit:
            self.save(update_fields=["quantity"])

    def decrease_stock(self, quantity: int, commit: bool = True):
        self.quantity = F("quantity") - quantity
        if commit:
            self.save(update_fields=["quantity"])


class AllocationQueryset(models.QuerySet):
    def annotate_stock_available_quantity(self):
        return self.annotate(
            stock_available_quantity=F("stock__quantity")
            - Coalesce(Sum("stock__allocations__quantity_allocated"), 0)
        )

    def available_quantity_for_stock(self, stock: "Stock"):
        allocated_quantity = (
            self.filter(stock=stock).aggregate(Sum("quantity_allocated"))[
                "quantity_allocated__sum"
            ]
            or 0
        )
        return max(stock.quantity - allocated_quantity, 0)


class Allocation(models.Model):
    order_line = models.ForeignKey(
        OrderLine,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    stock = models.ForeignKey(
        Stock,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    quantity_allocated = models.PositiveIntegerField(default=0)

    objects = models.Manager.from_queryset(AllocationQueryset)()

    class Meta:
        unique_together = [["order_line", "stock"]]
        ordering = ("pk",)


class PreorderAllocation(models.Model):
    order_line = models.ForeignKey(
        OrderLine,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="preorder_allocations",
    )
    quantity = models.PositiveIntegerField(default=0)
    product_variant_channel_listing = models.ForeignKey(
        ProductVariantChannelListing,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="preorder_allocations",
    )

    class Meta:
        unique_together = [["order_line", "product_variant_channel_listing"]]
        ordering = ("pk",)


class ReservationQuerySet(models.QuerySet):
    def not_expired(self):
        return self.filter(reserved_until__gt=timezone.now())

    def exclude_checkout_lines(self, checkout_lines: Optional[Iterable[CheckoutLine]]):
        if checkout_lines:
            return self.exclude(checkout_line__in=checkout_lines)

        return self


class PreorderReservation(models.Model):
    checkout_line = models.ForeignKey(
        CheckoutLine,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="preorder_reservations",
    )
    product_variant_channel_listing = models.ForeignKey(
        ProductVariantChannelListing,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="preorder_reservations",
    )
    quantity_reserved = models.PositiveIntegerField(default=0)
    reserved_until = models.DateTimeField()

    objects = models.Manager.from_queryset(ReservationQuerySet)()

    class Meta:
        unique_together = [["checkout_line", "product_variant_channel_listing"]]
        indexes = [
            models.Index(fields=["checkout_line", "reserved_until"]),
        ]
        ordering = ("pk",)


class Reservation(models.Model):
    checkout_line = models.ForeignKey(
        CheckoutLine,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    stock = models.ForeignKey(
        Stock,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    quantity_reserved = models.PositiveIntegerField(default=0)
    reserved_until = models.DateTimeField()

    objects = models.Manager.from_queryset(ReservationQuerySet)()

    class Meta:
        unique_together = [["checkout_line", "stock"]]
        indexes = [
            models.Index(fields=["checkout_line", "reserved_until"]),
        ]
        ordering = ("pk",)
