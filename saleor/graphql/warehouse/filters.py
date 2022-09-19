import django_filters
import graphene
from django.db.models import Exists, OuterRef, Q

from ...account.models import Address
from ...product.models import Product, ProductVariant
from ...warehouse import WarehouseClickAndCollectOption
from ...warehouse.models import Stock, Warehouse
from ..channel.types import Channel
from ..core.filters import (
    EnumFilter,
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    filter_slug_list,
)
from ..core.types import FilterInputObjectType
from ..utils import resolve_global_ids_to_primary_keys
from ..warehouse.enums import WarehouseClickAndCollectOptionEnum


def prefech_qs_for_filter(qs):
    return qs.prefetch_related("address")


def filter_search_warehouse(qs, _, value):
    if value:
        addresses = Address.objects.filter(
            Q(company_name__ilike=value)
            | Q(street_address_1__ilike=value)
            | Q(street_address_2__ilike=value)
            | Q(city__ilike=value)
            | Q(postal_code__ilike=value)
            | Q(phone__ilike=value)
        ).values("pk")
        qs = qs.filter(
            Q(name__ilike=value)
            | Q(email__ilike=value)
            | Q(Exists(addresses.filter(pk=OuterRef("address_id"))))
        )
    return qs


def filter_click_and_collect_option(qs, _, value):
    if value == WarehouseClickAndCollectOptionEnum.LOCAL.value:
        qs = qs.filter(
            click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
        )
    elif value == WarehouseClickAndCollectOptionEnum.ALL.value:
        qs = qs.filter(
            click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES
        )
    elif value == WarehouseClickAndCollectOptionEnum.DISABLED.value:
        qs = qs.filter(click_and_collect_option=WarehouseClickAndCollectOption.DISABLED)
    return qs


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, Channel)
        WarehouseChannel = Warehouse.channels.through
        warehouse_channels = WarehouseChannel.objects.filter(
            channel_id__in=channels_ids
        )
        qs = qs.filter(Exists(warehouse_channels.filter(warehouse_id=OuterRef("id"))))
    return qs


def filter_search_stock(qs, _, value):
    if value:
        products = Product.objects.filter(name__ilike=value).values("pk")
        variants = ProductVariant.objects.filter(
            Q(name__ilike=value) | Q(Exists(products.filter(pk=OuterRef("product_id"))))
        ).values("pk")
        addresses = Address.objects.filter(company_name__ilike=value)
        warehouses = Warehouse.objects.filter(
            Q(name__ilike=value)
            | Q(Exists(addresses.filter(id=OuterRef("address_id"))))
        ).values("pk")
        return qs.filter(
            Q(Exists(variants.filter(pk=OuterRef("product_variant_id"))))
            | Q(Exists(warehouses.filter(stock=OuterRef("pk"))))
        )
    return qs


class WarehouseFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search_warehouse)
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    is_private = django_filters.BooleanFilter(field_name="is_private")
    click_and_collect_option = EnumFilter(
        input_class=WarehouseClickAndCollectOptionEnum,
        method=filter_click_and_collect_option,
    )
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = Warehouse
        fields = ["click_and_collect_option"]


class WarehouseFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = WarehouseFilter


class StockFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search_stock)

    class Meta:
        model = Stock
        fields = ["quantity"]


class StockFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = StockFilter
