import functools
import operator

import django_filters
from django.db.models import Sum
from graphene_django.filter import GlobalIDFilter, GlobalIDMultipleChoiceFilter

from ...product.filters import MergedAttributes
from ...product.models import Attribute, Collection, Product, ProductType
from ...search.backends import picker
from ..core.filters import EnumFilter, ListObjectTypeFilter, ObjectTypeFilter
from ..core.types.common import PriceRangeInput
from ..utils import filter_by_query_param, get_nodes
from . import types
from .enums import (
    CollectionPublished,
    ProductTypeConfigurable,
    ProductTypeEnum,
    StockAvailability,
)
from .types.attributes import AttributeInput


def filter_products_by_attributes(qs, filter_value):
    attributes = Attribute.objects.prefetch_related("values")
    merged_attributes = MergedAttributes(attributes)

    # Convert attribute:value pairs into a list of query
    queries = []
    for attr_slug, value_slug in filter_value:
        query = merged_attributes.get_query(attr_slug, value_slug)
        queries.append(query)

    # Combine full query with AND operator.
    query = functools.reduce(operator.and_, queries)
    return qs.filter(query).distinct()


def filter_products_by_price(qs, price_lte=None, price_gte=None):
    if price_lte:
        qs = qs.filter(price__lte=price_lte)
    if price_gte:
        qs = qs.filter(price__gte=price_gte)
    return qs


def filter_products_by_categories(qs, categories):
    categories = [
        category.get_descendants(include_self=True) for category in categories
    ]
    ids = {category.id for tree in categories for category in tree}
    return qs.filter(category__in=ids)


def filter_products_by_collections(qs, collections):
    return qs.filter(collections__in=collections)


def sort_qs(qs, sort_by_product_order):
    if sort_by_product_order:
        qs = qs.order_by(
            sort_by_product_order["direction"] + sort_by_product_order["field"]
        )
    return qs


def filter_products_by_stock_availability(qs, stock_availability):
    qs = qs.annotate(total_quantity=Sum("variants__quantity"))
    if stock_availability == StockAvailability.IN_STOCK:
        qs = qs.filter(total_quantity__gt=0)
    elif stock_availability == StockAvailability.OUT_OF_STOCK:
        qs = qs.filter(total_quantity=0)
    return qs


def filter_attributes(qs, _, value):
    if value:
        value = [(v["slug"], v["value"]) for v in value]
        qs = filter_products_by_attributes(qs, value)
    return qs


def filter_categories(qs, _, value):
    if value:
        categories = get_nodes(value, types.Category)
        qs = filter_products_by_categories(qs, categories)
    return qs


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


def filter_collection_search(qs, _, value):
    search_fields = ("name", "slug")
    if value:
        qs = filter_by_query_param(qs, value, search_fields)
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


class ProductFilter(django_filters.FilterSet):
    is_published = django_filters.BooleanFilter()
    collections = GlobalIDMultipleChoiceFilter(method=filter_collections)
    categories = GlobalIDMultipleChoiceFilter(method=filter_categories)
    price = ObjectTypeFilter(input_class=PriceRangeInput, method=filter_price)
    attributes = ListObjectTypeFilter(
        input_class=AttributeInput, method=filter_attributes
    )
    stock_availability = EnumFilter(
        input_class=StockAvailability, method=filter_stock_availability
    )
    product_type = GlobalIDFilter()
    search = django_filters.CharFilter(method=filter_search)

    class Meta:
        model = Product
        fields = [
            "is_published",
            "collections",
            "categories",
            "price",
            "attributes",
            "stock_availability",
            "product_type",
            "search",
        ]


class CollectionFilter(django_filters.FilterSet):
    published = EnumFilter(
        input_class=CollectionPublished, method=filter_collection_publish
    )
    search = django_filters.CharFilter(method=filter_collection_search)

    class Meta:
        model = Collection
        fields = ["published", "search"]


class ProductTypeFilter(django_filters.FilterSet):
    configurable = EnumFilter(
        input_class=ProductTypeConfigurable, method=filter_product_type_configurable
    )

    product_type = EnumFilter(input_class=ProductTypeEnum, method=filter_product_type)

    class Meta:
        model = ProductType
        fields = ["configurable", "product_type"]
