import datetime

from django.db.models import Exists, OuterRef, Q, Subquery, Sum
from django.db.models.expressions import ExpressionWrapper
from django.db.models.fields import IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone

from ....channel.models import Channel
from ....product import ProductTypeKind
from ....product.models import (
    Category,
    CollectionProduct,
    ProductChannelListing,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ....product.search import search_products
from ....warehouse.models import Allocation, Reservation, Stock, Warehouse
from ...utils import resolve_global_ids_to_primary_keys
from ...utils.filters import (
    filter_range_field,
    filter_where_range_field_with_conditions,
)
from ...warehouse import types as warehouse_types
from .. import types as product_types
from ..enums import (
    StockAvailability,
)


def filter_products_by_variant_price(qs, channel_slug, price_lte=None, price_gte=None):
    channels = Channel.objects.using(qs.db).filter(slug=channel_slug).values("pk")
    product_variant_channel_listings = ProductVariantChannelListing.objects.using(
        qs.db
    ).filter(Exists(channels.filter(pk=OuterRef("channel_id"))))
    if price_lte:
        product_variant_channel_listings = product_variant_channel_listings.filter(
            Q(price_amount__lte=price_lte) | Q(price_amount__isnull=True)
        )
    if price_gte:
        product_variant_channel_listings = product_variant_channel_listings.filter(
            Q(price_amount__gte=price_gte) | Q(price_amount__isnull=True)
        )
    product_variant_channel_listings = product_variant_channel_listings.values(
        "variant_id"
    )
    variants = (
        ProductVariant.objects.using(qs.db)
        .filter(
            Exists(product_variant_channel_listings.filter(variant_id=OuterRef("pk")))
        )
        .values("product_id")
    )
    return qs.filter(Exists(variants.filter(product_id=OuterRef("pk"))))


def filter_products_by_minimal_price(
    qs, channel_slug, minimal_price_lte=None, minimal_price_gte=None
):
    channel = Channel.objects.using(qs.db).filter(slug=channel_slug).first()
    if not channel:
        return qs
    product_channel_listings = ProductChannelListing.objects.using(qs.db).filter(
        channel_id=channel.id
    )
    if minimal_price_lte:
        product_channel_listings = product_channel_listings.filter(
            discounted_price_amount__lte=minimal_price_lte
        )
    if minimal_price_gte:
        product_channel_listings = product_channel_listings.filter(
            discounted_price_amount__gte=minimal_price_gte
        )
    product_channel_listings = product_channel_listings.values("product_id")
    return qs.filter(Exists(product_channel_listings.filter(product_id=OuterRef("pk"))))


def filter_products_by_categories(qs, category_ids):
    categories = Category.objects.using(qs.db).filter(pk__in=category_ids)
    categories = (
        Category.tree.get_queryset_descendants(categories, include_self=True)
        .using(qs.db)
        .values("pk")
    )
    return qs.filter(Exists(categories.filter(pk=OuterRef("category_id"))))


def filter_products_by_collections(qs, collection_pks):
    collection_products = (
        CollectionProduct.objects.using(qs.db)
        .filter(collection_id__in=collection_pks)
        .values("product_id")
    )
    return qs.filter(Exists(collection_products.filter(product_id=OuterRef("pk"))))


def filter_products_by_stock_availability(qs, stock_availability, channel_slug):
    allocations = (
        Allocation.objects.using(qs.db)
        .values("stock_id")
        .filter(quantity_allocated__gt=0, stock_id=OuterRef("pk"))
        .values_list(Sum("quantity_allocated"))
    )
    allocated_subquery = Subquery(queryset=allocations, output_field=IntegerField())

    reservations = (
        Reservation.objects.using(qs.db)
        .values("stock_id")
        .filter(
            quantity_reserved__gt=0,
            stock_id=OuterRef("pk"),
            reserved_until__gt=timezone.now(),
        )
        .values_list(Sum("quantity_reserved"))
    )
    reservation_subquery = Subquery(queryset=reservations, output_field=IntegerField())
    warehouse_pks = list(
        Warehouse.objects.using(qs.db)
        .for_channel_with_active_shipping_zone_or_cc(channel_slug)
        .values_list("pk", flat=True)
    )
    stocks = (
        Stock.objects.using(qs.db)
        .filter(
            warehouse_id__in=warehouse_pks,
            quantity__gt=Coalesce(allocated_subquery, 0)
            + Coalesce(reservation_subquery, 0),
        )
        .values("product_variant_id")
    )

    variants = (
        ProductVariant.objects.using(qs.db)
        .filter(Exists(stocks.filter(product_variant_id=OuterRef("pk"))))
        .values("product_id")
    )
    if stock_availability == StockAvailability.IN_STOCK:
        qs = qs.filter(Exists(variants.filter(product_id=OuterRef("pk"))))
    if stock_availability == StockAvailability.OUT_OF_STOCK:
        qs = qs.filter(~Exists(variants.filter(product_id=OuterRef("pk"))))
    return qs


def filter_categories(qs, _, value):
    if value:
        _, category_pks = resolve_global_ids_to_primary_keys(
            value, product_types.Category
        )
        qs = filter_products_by_categories(qs, category_pks)
    return qs


def filter_product_types(qs, _, value):
    if not value:
        return qs
    _, product_type_pks = resolve_global_ids_to_primary_keys(
        value, product_types.ProductType
    )
    return qs.filter(product_type_id__in=product_type_pks)


def filter_has_category(qs, _, value):
    return qs.filter(category__isnull=not value)


def filter_has_preordered_variants(qs, _, value):
    variants = (
        ProductVariant.objects.using(qs.db)
        .filter(is_preorder=True)
        .filter(
            Q(preorder_end_date__isnull=True) | Q(preorder_end_date__gt=timezone.now())
        )
        .values("product_id")
    )
    if value:
        return qs.filter(Exists(variants.filter(product_id=OuterRef("pk"))))
    return qs.filter(~Exists(variants.filter(product_id=OuterRef("pk"))))


def filter_collections(qs, _, value):
    if value:
        _, collection_pks = resolve_global_ids_to_primary_keys(
            value, product_types.Collection
        )
        qs = filter_products_by_collections(qs, collection_pks)
    return qs


def filter_products_is_published(qs, _, value, channel_slug):
    channel = Channel.objects.using(qs.db).filter(slug=channel_slug).values("pk")
    product_channel_listings = (
        ProductChannelListing.objects.using(qs.db)
        .filter(Exists(channel.filter(pk=OuterRef("channel_id"))), is_published=value)
        .values("product_id")
    )

    # Filter out product for which there is no variant with price
    variant_channel_listings = (
        ProductVariantChannelListing.objects.using(qs.db)
        .filter(
            Exists(channel.filter(pk=OuterRef("channel_id"))),
            price_amount__isnull=False,
        )
        .values("id")
    )
    variants = (
        ProductVariant.objects.using(qs.db)
        .filter(Exists(variant_channel_listings.filter(variant_id=OuterRef("pk"))))
        .values("product_id")
    )

    return qs.filter(
        Exists(product_channel_listings.filter(product_id=OuterRef("pk"))),
        Exists(variants.filter(product_id=OuterRef("pk"))),
    )


def filter_products_is_available(qs, _, value, channel_slug):
    channel = Channel.objects.using(qs.db).filter(slug=channel_slug).values("pk")
    now = datetime.datetime.now(tz=datetime.UTC)
    if value:
        product_channel_listings = (
            ProductChannelListing.objects.using(qs.db)
            .filter(
                Exists(channel.filter(pk=OuterRef("channel_id"))),
                available_for_purchase_at__lte=now,
            )
            .values("product_id")
        )
    else:
        product_channel_listings = (
            ProductChannelListing.objects.using(qs.db)
            .filter(
                Exists(channel.filter(pk=OuterRef("channel_id"))),
                Q(available_for_purchase_at__gt=now)
                | Q(available_for_purchase_at__isnull=True),
            )
            .values("product_id")
        )

    return qs.filter(Exists(product_channel_listings.filter(product_id=OuterRef("pk"))))


def filter_products_channel_field_from_date(qs, _, value, channel_slug, field):
    channel = Channel.objects.using(qs.db).filter(slug=channel_slug).values("pk")
    lookup = {
        f"{field}__lte": value,
    }
    product_channel_listings = (
        ProductChannelListing.objects.using(qs.db)
        .filter(
            Exists(channel.filter(pk=OuterRef("channel_id"))),
            **lookup,
        )
        .values("product_id")
    )

    return qs.filter(Exists(product_channel_listings.filter(product_id=OuterRef("pk"))))


def filter_products_visible_in_listing(qs, _, value, channel_slug):
    channel = Channel.objects.using(qs.db).filter(slug=channel_slug).values("pk")
    product_channel_listings = (
        ProductChannelListing.objects.using(qs.db)
        .filter(
            Exists(channel.filter(pk=OuterRef("channel_id"))), visible_in_listings=value
        )
        .values("product_id")
    )

    return qs.filter(Exists(product_channel_listings.filter(product_id=OuterRef("pk"))))


def filter_variant_price(qs, _, value, channel_slug):
    qs = filter_products_by_variant_price(
        qs, channel_slug, price_lte=value.get("lte"), price_gte=value.get("gte")
    )
    return qs


def filter_minimal_price(qs, _, value, channel_slug):
    qs = filter_products_by_minimal_price(
        qs,
        channel_slug,
        minimal_price_lte=value.get("lte"),
        minimal_price_gte=value.get("gte"),
    )
    return qs


def filter_stock_availability(qs, _, value, channel_slug):
    if value:
        qs = filter_products_by_stock_availability(qs, value, channel_slug)
    return qs


def filter_search(qs, _, value):
    return search_products(qs, value)


def filter_gift_card(qs, _, value):
    product_types = ProductType.objects.using(qs.db).filter(
        kind=ProductTypeKind.GIFT_CARD
    )
    lookup = Exists(product_types.filter(id=OuterRef("product_type_id")))
    return qs.filter(lookup) if value is True else qs.exclude(lookup)


def filter_stocks(qs, _, value):
    warehouse_ids = value.get("warehouse_ids")
    quantity = value.get("quantity")
    if warehouse_ids and not quantity:
        return filter_warehouses(qs, _, warehouse_ids)
    if quantity and not warehouse_ids:
        return filter_quantity(qs, quantity)
    if quantity and warehouse_ids:
        return filter_quantity(qs, quantity, warehouse_ids)
    return qs


def filter_warehouses(qs, _, value):
    if value:
        _, warehouse_pks = resolve_global_ids_to_primary_keys(
            value, warehouse_types.Warehouse
        )
        warehouses = (
            Warehouse.objects.using(qs.db).filter(pk__in=warehouse_pks).values("pk")
        )
        variant_ids = (
            Stock.objects.using(qs.db)
            .filter(Exists(warehouses.filter(pk=OuterRef("warehouse"))))
            .values("product_variant_id")
        )
        variants = (
            ProductVariant.objects.using(qs.db).filter(id__in=variant_ids).values("pk")
        )
        return qs.filter(Exists(variants.filter(product=OuterRef("pk"))))
    return qs


def filter_quantity(qs, quantity_value, warehouse_ids=None):
    """Filter products queryset by product variants quantity.

    Return product queryset which contains at least one variant with aggregated quantity
    between given range. If warehouses is given, it aggregates quantity only
    from stocks which are in given warehouses.
    """
    stocks = Stock.objects.using(qs.db).all()
    if warehouse_ids:
        _, warehouse_pks = resolve_global_ids_to_primary_keys(
            warehouse_ids, warehouse_types.Warehouse
        )
        stocks = stocks.filter(warehouse_id__in=warehouse_pks)
    stocks = stocks.values("product_variant_id").filter(
        product_variant_id=OuterRef("pk")
    )

    stocks = Subquery(stocks.values_list(Sum("quantity")))
    variants = ProductVariant.objects.using(qs.db).annotate(
        total_quantity=ExpressionWrapper(stocks, output_field=IntegerField())
    )
    variants = list(
        filter_range_field(variants, "total_quantity", quantity_value).values_list(
            "product_id", flat=True
        )
    )
    return qs.filter(pk__in=variants)


def where_filter_products_is_available(qs, _, value, channel_slug):
    if value is None:
        return qs.none()
    channel = Channel.objects.using(qs.db).filter(slug=channel_slug).values("pk")
    now = datetime.datetime.now(tz=datetime.UTC)
    if value:
        product_channel_listings = (
            ProductChannelListing.objects.using(qs.db)
            .filter(
                Exists(channel.filter(pk=OuterRef("channel_id"))),
                available_for_purchase_at__lte=now,
            )
            .values("product_id")
        )
    else:
        product_channel_listings = (
            ProductChannelListing.objects.using(qs.db)
            .filter(
                Exists(channel.filter(pk=OuterRef("channel_id"))),
                Q(available_for_purchase_at__gt=now)
                | Q(available_for_purchase_at__isnull=True),
            )
            .values("product_id")
        )

    return qs.filter(Exists(product_channel_listings.filter(product_id=OuterRef("pk"))))


def where_filter_products_channel_field_from_date(qs, _, value, channel_slug, field):
    if value is None:
        return qs.none()
    channel = Channel.objects.using(qs.db).filter(slug=channel_slug).values("pk")
    lookup = {
        f"{field}__lte": value,
    }
    product_channel_listings = (
        ProductChannelListing.objects.using(qs.db)
        .filter(
            Exists(channel.filter(pk=OuterRef("channel_id"))),
            **lookup,
        )
        .values("product_id")
    )

    return qs.filter(Exists(product_channel_listings.filter(product_id=OuterRef("pk"))))


def where_filter_has_category(qs, _, value):
    if value is None:
        return qs.none()
    return qs.filter(category__isnull=not value)


def where_filter_stocks(qs, _, value):
    if not value:
        return qs.none()
    warehouse_ids = value.get("warehouse_ids")
    quantity = value.get("quantity")
    if warehouse_ids and not quantity:
        return where_filter_warehouses(qs, _, warehouse_ids)
    if quantity and not warehouse_ids:
        return where_filter_quantity(qs, quantity)
    if quantity and warehouse_ids:
        return where_filter_quantity(qs, quantity, warehouse_ids)
    return qs.none()


def where_filter_warehouses(qs, _, value):
    if not value:
        return qs.none()
    _, warehouse_pks = resolve_global_ids_to_primary_keys(
        value, warehouse_types.Warehouse
    )
    warehouses = (
        Warehouse.objects.using(qs.db).filter(pk__in=warehouse_pks).values("pk")
    )
    variant_ids = (
        Stock.objects.using(qs.db)
        .filter(Exists(warehouses.filter(pk=OuterRef("warehouse"))))
        .values("product_variant_id")
    )
    variants = (
        ProductVariant.objects.using(qs.db).filter(id__in=variant_ids).values("pk")
    )
    return qs.filter(Exists(variants.filter(product=OuterRef("pk"))))


def where_filter_quantity(qs, quantity_value, warehouse_ids=None):
    """Filter products queryset by product variants quantity.

    Return product queryset which contains at least one variant with aggregated quantity
    between given range. If warehouses is given, it aggregates quantity only
    from stocks which are in given warehouses.
    """
    stocks = Stock.objects.using(qs.db).all()
    if warehouse_ids:
        _, warehouse_pks = resolve_global_ids_to_primary_keys(
            warehouse_ids, warehouse_types.Warehouse
        )
        stocks = stocks.filter(warehouse_id__in=warehouse_pks)
    stocks = stocks.values("product_variant_id").filter(
        product_variant_id=OuterRef("pk")
    )

    stocks = Subquery(stocks.values_list(Sum("quantity")))
    variants = ProductVariant.objects.using(qs.db).annotate(
        total_quantity=ExpressionWrapper(stocks, output_field=IntegerField())
    )
    variants = list(
        _filter_range(variants, "total_quantity", quantity_value).values_list(
            "product_id", flat=True
        )
    )
    return qs.filter(pk__in=variants)


def _filter_range(qs, field, value):
    gte, lte = value.get("gte"), value.get("lte")
    if gte is None and lte is None:
        return qs.none()
    return filter_range_field(qs, field, value)


def where_filter_stock_availability(qs, _, value, channel_slug):
    if value:
        return filter_products_by_stock_availability(qs, value, channel_slug)
    return qs.none()


def where_filter_gift_card(qs, _, value):
    if value is None:
        return qs.none()

    product_types = ProductType.objects.using(qs.db).filter(
        kind=ProductTypeKind.GIFT_CARD
    )
    lookup = Exists(product_types.filter(id=OuterRef("product_type_id")))
    return qs.filter(lookup) if value is True else qs.exclude(lookup)


def where_filter_has_preordered_variants(qs, _, value):
    if value is None:
        return qs.none()

    variants = (
        ProductVariant.objects.using(qs.db)
        .filter(is_preorder=True)
        .filter(
            Q(preorder_end_date__isnull=True) | Q(preorder_end_date__gt=timezone.now())
        )
        .values("product_id")
    )
    if value:
        return qs.filter(Exists(variants.filter(product_id=OuterRef("pk"))))
    return qs.filter(~Exists(variants.filter(product_id=OuterRef("pk"))))


def where_filter_updated_at_range(qs, _, value):
    if value is None:
        return qs.none()
    return filter_where_range_field_with_conditions(qs, "updated_at", value)


def where_filter_by_categories(qs, value):
    """Filter products by categories and subcategories of provided categories."""
    if not value:
        return qs.none()
    eq = value.get("eq")
    one_of = value.get("one_of")
    pks = None
    if eq and isinstance(eq, str):
        _, pks = resolve_global_ids_to_primary_keys([eq], "Category", True)
    if one_of:
        _, pks = resolve_global_ids_to_primary_keys(one_of, "Category", True)
    if pks:
        return filter_products_by_categories(qs, pks)
    return qs.none()
