from collections import defaultdict
from typing import Dict, List, Optional

import django_filters
import graphene
from django.db.models import F, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from graphene_django.filter import GlobalIDFilter, GlobalIDMultipleChoiceFilter

from ...product.filters import filter_products_by_attributes_values
from ...product.models import (
    Attribute,
    Category,
    Collection,
    Product,
    ProductType,
    ProductVariant,
)
from ...search.backends import picker
from ...warehouse.models import Stock
from ..core.filters import EnumFilter, ListObjectTypeFilter, ObjectTypeFilter
from ..core.types import FilterInputObjectType
from ..core.types.common import IntRangeInput, PriceRangeInput
from ..core.utils import from_global_id_strict_type
from ..utils import get_nodes, resolve_global_ids_to_primary_keys
from ..utils.filters import filter_by_query_param, filter_range_field
from ..warehouse import types as warehouse_types
from . import types
from .enums import (
    CollectionPublished,
    ProductTypeConfigurable,
    ProductTypeEnum,
    StockAvailability,
)
from .types.attributes import AttributeInput


def filter_fields_containing_value(*search_fields: str):
    """Create a icontains filters through given fields on a given query set object."""

    def _filter_qs(qs, _, value):
        if value:
            qs = filter_by_query_param(qs, value, search_fields)
        return qs

    return _filter_qs


def _clean_product_attributes_filter_input(
    filter_value,
) -> Dict[int, List[Optional[int]]]:
    attributes = Attribute.objects.prefetch_related("values")
    attributes_map: Dict[str, int] = {
        attribute.slug: attribute.pk for attribute in attributes
    }
    values_map: Dict[str, Dict[str, int]] = {
        attr.slug: {value.slug: value.pk for value in attr.values.all()}
        for attr in attributes
    }
    queries: Dict[int, List[Optional[int]]] = defaultdict(list)
    # Convert attribute:value pairs into a dictionary where
    # attributes are keys and values are grouped in lists
    for attr_name, val_slugs in filter_value:
        if attr_name not in attributes_map:
            raise ValueError("Unknown attribute name: %r" % (attr_name,))
        attr_pk = attributes_map[attr_name]
        attr_val_pk = [
            values_map[attr_name][val_slug]
            for val_slug in val_slugs
            if val_slug in values_map[attr_name]
        ]
        queries[attr_pk] += attr_val_pk

    return queries


def filter_products_by_attributes(qs, filter_value):
    queries = _clean_product_attributes_filter_input(filter_value)
    return filter_products_by_attributes_values(qs, queries)


def filter_products_by_price(qs, price_lte=None, price_gte=None):
    if price_lte:
        qs = qs.filter(price_amount__lte=price_lte)
    if price_gte:
        qs = qs.filter(price_amount__gte=price_gte)
    return qs


def filter_products_by_minimal_price(
    qs, minimal_price_lte=None, minimal_price_gte=None
):
    if minimal_price_lte:
        qs = qs.filter(minimal_variant_price_amount__lte=minimal_price_lte)
    if minimal_price_gte:
        qs = qs.filter(minimal_variant_price_amount__gte=minimal_price_gte)
    return qs


def filter_products_by_categories(qs, categories):
    categories = [
        category.get_descendants(include_self=True) for category in categories
    ]
    ids = {category.id for tree in categories for category in tree}
    return qs.filter(category__in=ids)


def filter_products_by_collections(qs, collections):
    return qs.filter(collections__in=collections)


def filter_products_by_stock_availability(qs, stock_availability):
    total_stock = (
        Stock.objects.select_related("product_variant")
        .values("product_variant__product_id")
        .annotate(
            total_quantity_allocated=Coalesce(Sum("allocations__quantity_allocated"), 0)
        )
        .annotate(total_quantity=Coalesce(Sum("quantity"), 0))
        .annotate(total_available=F("total_quantity") - F("total_quantity_allocated"))
        .filter(total_available__lte=0)
        .values_list("product_variant__product_id", flat=True)
    )
    if stock_availability == StockAvailability.IN_STOCK:
        qs = qs.exclude(id__in=Subquery(total_stock))
    elif stock_availability == StockAvailability.OUT_OF_STOCK:
        qs = qs.filter(id__in=Subquery(total_stock))
    return qs


def filter_attributes(qs, _, value):
    if value:
        value_list = []
        for v in value:
            slug = v["slug"]
            values = [v["value"]] if "value" in v else v.get("values", [])
            value_list.append((slug, values))
        qs = filter_products_by_attributes(qs, value_list)
    return qs


def filter_categories(qs, _, value):
    if value:
        categories = get_nodes(value, types.Category)
        qs = filter_products_by_categories(qs, categories)
    return qs


def filter_has_category(qs, _, value):
    return qs.filter(category__isnull=not value)


def filter_collections(qs, _, value):
    if value:
        collections = get_nodes(value, types.Collection)
        qs = filter_products_by_collections(qs, collections)
    return qs


def filter_price(qs, _, value):
    qs = filter_products_by_price(
        qs, price_lte=value.get("lte"), price_gte=value.get("gte")
    )
    return qs


def filter_minimal_price(qs, _, value):
    qs = filter_products_by_minimal_price(
        qs, minimal_price_lte=value.get("lte"), minimal_price_gte=value.get("gte")
    )
    return qs


def filter_stock_availability(qs, _, value):
    if value:
        qs = filter_products_by_stock_availability(qs, value)
    return qs


def filter_search(qs, _, value):
    if value:
        search = picker.pick_backend()
        qs &= search(value).distinct()
    return qs


def filter_collection_publish(qs, _, value):
    if value == CollectionPublished.PUBLISHED:
        qs = qs.filter(is_published=True)
    elif value == CollectionPublished.HIDDEN:
        qs = qs.filter(is_published=False)
    return qs


def filter_product_type_configurable(qs, _, value):
    if value == ProductTypeConfigurable.CONFIGURABLE:
        qs = qs.filter(has_variants=True)
    elif value == ProductTypeConfigurable.SIMPLE:
        qs = qs.filter(has_variants=False)
    return qs


def filter_product_type(qs, _, value):
    if value == ProductTypeEnum.DIGITAL:
        qs = qs.filter(is_digital=True)
    elif value == ProductTypeEnum.SHIPPABLE:
        qs = qs.filter(is_shipping_required=True)
    return qs


def filter_attributes_by_product_types(qs, field, value):
    if not value:
        return qs

    if field == "in_category":
        category_id = from_global_id_strict_type(
            value, only_type="Category", field=field
        )
        category = Category.objects.filter(pk=category_id).first()

        if category is None:
            return qs.none()

        tree = category.get_descendants(include_self=True)
        product_qs = Product.objects.filter(category__in=tree)

    elif field == "in_collection":
        collection_id = from_global_id_strict_type(
            value, only_type="Collection", field=field
        )
        product_qs = Product.objects.filter(collections__id=collection_id)

    else:
        raise NotImplementedError(f"Filtering by {field} is unsupported")

    product_types = set(product_qs.values_list("product_type_id", flat=True))
    return qs.filter(
        Q(product_types__in=product_types) | Q(product_variant_types__in=product_types)
    )


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
        return qs.filter(variants__stocks__warehouse__pk__in=warehouse_pks)
    return qs


def filter_quantity(qs, quantity_value, warehouses=None):
    """Filter products queryset by product variants quantity.

    Return product queryset which contains at least one variant with aggregated quantity
    between given range. If warehouses is given, it aggregates quantity only
    from stocks which are in given warehouses.
    """
    product_variants = ProductVariant.objects.filter(product__in=qs)
    if warehouses:
        _, warehouse_pks = resolve_global_ids_to_primary_keys(
            warehouses, warehouse_types.Warehouse
        )
        product_variants = product_variants.annotate(
            total_quantity=Sum(
                "stocks__quantity", filter=Q(stocks__warehouse__pk__in=warehouse_pks)
            )
        )
    else:
        product_variants = product_variants.annotate(
            total_quantity=Sum("stocks__quantity")
        )

    product_variants = filter_range_field(
        product_variants, "total_quantity", quantity_value
    )
    return qs.filter(variants__in=product_variants)


class ProductStockFilterInput(graphene.InputObjectType):
    warehouse_ids = graphene.List(graphene.NonNull(graphene.ID), required=False)
    quantity = graphene.Field(IntRangeInput, required=False)


class ProductFilter(django_filters.FilterSet):
    is_published = django_filters.BooleanFilter()
    collections = GlobalIDMultipleChoiceFilter(method=filter_collections)
    categories = GlobalIDMultipleChoiceFilter(method=filter_categories)
    has_category = django_filters.BooleanFilter(method=filter_has_category)
    price = ObjectTypeFilter(
        input_class=PriceRangeInput, method=filter_price, field_name="price_amount"
    )
    minimal_price = ObjectTypeFilter(
        input_class=PriceRangeInput,
        method=filter_minimal_price,
        field_name="minimal_price_amount",
    )
    attributes = ListObjectTypeFilter(
        input_class=AttributeInput, method=filter_attributes
    )
    stock_availability = EnumFilter(
        input_class=StockAvailability, method=filter_stock_availability
    )
    product_type = GlobalIDFilter()  # Deprecated
    product_types = GlobalIDMultipleChoiceFilter(field_name="product_type")
    stocks = ObjectTypeFilter(input_class=ProductStockFilterInput, method=filter_stocks)
    search = django_filters.CharFilter(method=filter_search)

    class Meta:
        model = Product
        fields = [
            "is_published",
            "collections",
            "categories",
            "has_category",
            "price",
            "attributes",
            "stock_availability",
            "product_type",
            "stocks",
            "search",
        ]


class CollectionFilter(django_filters.FilterSet):
    published = EnumFilter(
        input_class=CollectionPublished, method=filter_collection_publish
    )
    search = django_filters.CharFilter(
        method=filter_fields_containing_value("slug", "name")
    )
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = Collection
        fields = ["published", "search"]


class CategoryFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method=filter_fields_containing_value("slug", "name", "description")
    )
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = Category
        fields = ["search"]


class ProductTypeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method=filter_fields_containing_value("name", "slug")
    )

    configurable = EnumFilter(
        input_class=ProductTypeConfigurable, method=filter_product_type_configurable
    )

    product_type = EnumFilter(input_class=ProductTypeEnum, method=filter_product_type)
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = ProductType
        fields = ["search", "configurable", "product_type"]


class AttributeFilter(django_filters.FilterSet):
    # Search by attribute name and slug
    search = django_filters.CharFilter(
        method=filter_fields_containing_value("slug", "name")
    )
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    in_collection = GlobalIDFilter(method=filter_attributes_by_product_types)
    in_category = GlobalIDFilter(method=filter_attributes_by_product_types)

    class Meta:
        model = Attribute
        fields = [
            "value_required",
            "is_variant_only",
            "visible_in_storefront",
            "filterable_in_storefront",
            "filterable_in_dashboard",
            "available_in_grid",
        ]


class ProductFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductFilter


class CollectionFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CollectionFilter


class CategoryFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CategoryFilter


class ProductTypeFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductTypeFilter


class AttributeFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = AttributeFilter
