import datetime
import math
from collections import defaultdict
from typing import Dict, Iterable, List, Optional

import django_filters
import graphene
import pytz
from django.db.models import Exists, FloatField, OuterRef, Q, Subquery, Sum
from django.db.models.expressions import ExpressionWrapper
from django.db.models.fields import IntegerField
from django.db.models.functions import Cast, Coalesce
from django.utils import timezone

from ...attribute import AttributeInputType
from ...attribute.models import (
    AssignedProductAttribute,
    AssignedProductAttributeValue,
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    Attribute,
    AttributeValue,
)
from ...channel.models import Channel
from ...product import ProductTypeKind
from ...product.models import (
    Category,
    Collection,
    CollectionProduct,
    Product,
    ProductChannelListing,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ...product.search import search_products
from ...warehouse.models import Allocation, Stock, Warehouse
from ..channel.filters import get_channel_slug_from_filter_data
from ..core.filters import (
    EnumFilter,
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types import (
    ChannelFilterInputObjectType,
    DateTimeRangeInput,
    FilterInputObjectType,
    IntRangeInput,
    NonNullList,
    PriceRangeInput,
)
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_by_id, filter_range_field
from ..warehouse import types as warehouse_types
from . import types as product_types
from .enums import (
    CollectionPublished,
    ProductTypeConfigurable,
    ProductTypeEnum,
    ProductTypeKindEnum,
    StockAvailability,
)

T_PRODUCT_FILTER_QUERIES = Dict[int, Iterable[int]]


def _clean_product_attributes_filter_input(filter_value, queries):
    attribute_slugs = []
    value_slugs = []
    for attr_slug, val_slugs in filter_value:
        attribute_slugs.append(attr_slug)
        value_slugs.extend(val_slugs)
    attributes_slug_pk_map: Dict[str, int] = {}
    attributes_pk_slug_map: Dict[int, str] = {}
    values_map: Dict[str, Dict[str, int]] = defaultdict(dict)
    for attr_slug, attr_pk in Attribute.objects.filter(
        slug__in=attribute_slugs
    ).values_list("slug", "id"):
        attributes_slug_pk_map[attr_slug] = attr_pk
        attributes_pk_slug_map[attr_pk] = attr_slug

    for (attr_pk, value_pk, value_slug,) in AttributeValue.objects.filter(
        slug__in=value_slugs, attribute_id__in=attributes_pk_slug_map.keys()
    ).values_list("attribute_id", "pk", "slug"):
        attr_slug = attributes_pk_slug_map[attr_pk]
        values_map[attr_slug][value_slug] = value_pk

    # Convert attribute:value pairs into a dictionary where
    # attributes are keys and values are grouped in lists
    for attr_name, val_slugs in filter_value:
        if attr_name not in attributes_slug_pk_map:
            raise ValueError("Unknown attribute name: %r" % (attr_name,))
        attr_pk = attributes_slug_pk_map[attr_name]
        attr_val_pk = [
            values_map[attr_name][val_slug]
            for val_slug in val_slugs
            if val_slug in values_map[attr_name]
        ]
        queries[attr_pk] += attr_val_pk


def _clean_product_attributes_range_filter_input(filter_value, queries):
    attributes = Attribute.objects.filter(input_type=AttributeInputType.NUMERIC)
    values = (
        AttributeValue.objects.filter(
            Exists(attributes.filter(pk=OuterRef("attribute_id")))
        )
        .annotate(numeric_value=Cast("name", FloatField()))
        .select_related("attribute")
    )

    attributes_map: Dict[str, int] = {}
    values_map: Dict[str, Dict[str, int]] = defaultdict(dict)
    for value_data in values.values_list(
        "attribute_id", "attribute__slug", "pk", "numeric_value"
    ):
        attr_pk, attr_slug, pk, numeric_value = value_data
        attributes_map[attr_slug] = attr_pk
        values_map[attr_slug][numeric_value] = pk

    for attr_name, val_range in filter_value:
        if attr_name not in attributes_map:
            raise ValueError("Unknown numeric attribute name: %r" % (attr_name,))
        gte, lte = val_range.get("gte", 0), val_range.get("lte", math.inf)
        attr_pk = attributes_map[attr_name]
        attr_values = values_map[attr_name]
        matching_values = [
            value for value in attr_values.keys() if gte <= value and lte >= value
        ]
        attr_val_pks = [attr_values[value] for value in matching_values]
        queries[attr_pk] += attr_val_pks


def _clean_product_attributes_date_time_range_filter_input(filter_value):
    attribute_slugs = [slug for slug, _ in filter_value]
    matching_attributes = AttributeValue.objects.filter(
        attribute__slug__in=attribute_slugs
    )
    filters = {}
    for _, val_range in filter_value:
        if lte := val_range.get("lte"):
            if not isinstance(lte, datetime.datetime):
                lte = datetime.datetime.combine(
                    lte, datetime.datetime.max.time(), tzinfo=pytz.UTC
                )
            filters["date_time__lte"] = lte
        if gte := val_range.get("gte"):
            if not isinstance(gte, datetime.datetime):
                gte = datetime.datetime.combine(
                    gte, datetime.datetime.min.time(), tzinfo=pytz.UTC
                )
            filters["date_time__gte"] = gte
    return matching_attributes.filter(**filters)


def _clean_product_attributes_boolean_filter_input(filter_value, queries):
    attribute_slugs = [slug for slug, _ in filter_value]
    attributes = Attribute.objects.filter(
        input_type=AttributeInputType.BOOLEAN, slug__in=attribute_slugs
    ).prefetch_related("values")
    values_map = {
        attr.slug: {
            "pk": attr.pk,
            "values": {val.boolean: val.pk for val in attr.values.all()},
        }
        for attr in attributes
    }

    for attr_slug, val in filter_value:
        attr_pk = values_map[attr_slug]["pk"]
        value_pk = values_map[attr_slug]["values"].get(val)
        if value_pk:
            queries[attr_pk] += [value_pk]


def filter_products_by_attributes_values(qs, queries: T_PRODUCT_FILTER_QUERIES):
    filters = []
    for values in queries.values():
        assigned_product_attribute_values = (
            AssignedProductAttributeValue.objects.filter(value_id__in=values)
        )
        assigned_product_attributes = AssignedProductAttribute.objects.filter(
            Exists(
                assigned_product_attribute_values.filter(assignment_id=OuterRef("pk"))
            )
        )
        product_attribute_filter = Q(
            Exists(assigned_product_attributes.filter(product_id=OuterRef("pk")))
        )

        assigned_variant_attribute_values = (
            AssignedVariantAttributeValue.objects.filter(value_id__in=values)
        )
        assigned_variant_attributes = AssignedVariantAttribute.objects.filter(
            Exists(
                assigned_variant_attribute_values.filter(assignment_id=OuterRef("pk"))
            )
        )
        product_variants = ProductVariant.objects.filter(
            Exists(assigned_variant_attributes.filter(variant_id=OuterRef("pk")))
        )
        variant_attribute_filter = Q(
            Exists(product_variants.filter(product_id=OuterRef("pk")))
        )

        filters.append(product_attribute_filter | variant_attribute_filter)

    return qs.filter(*filters)


def filter_products_by_attributes_values_qs(qs, values_qs):
    assigned_product_attribute_values = AssignedProductAttributeValue.objects.filter(
        value__in=values_qs
    )
    assigned_product_attributes = AssignedProductAttribute.objects.filter(
        Exists(assigned_product_attribute_values.filter(assignment_id=OuterRef("pk")))
    )
    product_attribute_filter = Q(
        Exists(assigned_product_attributes.filter(product_id=OuterRef("pk")))
    )

    assigned_variant_attribute_values = AssignedVariantAttributeValue.objects.filter(
        value__in=values_qs
    )
    assigned_variant_attributes = AssignedVariantAttribute.objects.filter(
        Exists(assigned_variant_attribute_values.filter(assignment_id=OuterRef("pk")))
    )
    product_variants = ProductVariant.objects.filter(
        Exists(assigned_variant_attributes.filter(variant_id=OuterRef("pk")))
    )
    variant_attribute_filter = Q(
        Exists(product_variants.filter(product_id=OuterRef("pk")))
    )

    return qs.filter(product_attribute_filter | variant_attribute_filter)


def filter_products_by_attributes(
    qs,
    filter_values,
    filter_range_values,
    filter_boolean_values,
    date_range_list,
    date_time_range_list,
):
    queries: Dict[int, List[Optional[int]]] = defaultdict(list)
    try:
        if filter_values:
            _clean_product_attributes_filter_input(filter_values, queries)
        if filter_range_values:
            _clean_product_attributes_range_filter_input(filter_range_values, queries)
        if date_range_list:
            values_qs = _clean_product_attributes_date_time_range_filter_input(
                date_range_list
            )
            return filter_products_by_attributes_values_qs(qs, values_qs)
        if date_time_range_list:
            values_qs = _clean_product_attributes_date_time_range_filter_input(
                date_time_range_list
            )
            return filter_products_by_attributes_values_qs(qs, values_qs)
        if filter_boolean_values:
            _clean_product_attributes_boolean_filter_input(
                filter_boolean_values, queries
            )
    except ValueError:
        return Product.objects.none()
    return filter_products_by_attributes_values(qs, queries)


def filter_products_by_variant_price(qs, channel_slug, price_lte=None, price_gte=None):
    channels = Channel.objects.filter(slug=channel_slug).values("pk")
    product_variant_channel_listings = ProductVariantChannelListing.objects.filter(
        Exists(channels.filter(pk=OuterRef("channel_id")))
    )
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
    variants = ProductVariant.objects.filter(
        Exists(product_variant_channel_listings.filter(variant_id=OuterRef("pk")))
    ).values("product_id")
    return qs.filter(Exists(variants.filter(product_id=OuterRef("pk"))))


def filter_products_by_minimal_price(
    qs, channel_slug, minimal_price_lte=None, minimal_price_gte=None
):
    channel = Channel.objects.filter(slug=channel_slug).first()
    if not channel:
        return qs
    product_channel_listings = ProductChannelListing.objects.filter(
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
    categories = Category.objects.filter(pk__in=category_ids)
    categories = Category.tree.get_queryset_descendants(
        categories, include_self=True
    ).values("pk")
    return qs.filter(Exists(categories.filter(pk=OuterRef("category_id"))))


def filter_products_by_collections(qs, collection_pks):
    collection_products = CollectionProduct.objects.filter(
        collection_id__in=collection_pks
    ).values("product_id")
    return qs.filter(Exists(collection_products.filter(product_id=OuterRef("pk"))))


def filter_products_by_stock_availability(qs, stock_availability, channel_slug):
    allocations = (
        Allocation.objects.values("stock_id")
        .filter(quantity_allocated__gt=0, stock_id=OuterRef("pk"))
        .values_list(Sum("quantity_allocated"))
    )
    allocated_subquery = Subquery(queryset=allocations, output_field=IntegerField())

    stocks = (
        Stock.objects.for_channel_and_country(channel_slug)
        .filter(quantity__gt=Coalesce(allocated_subquery, 0))
        .values("product_variant_id")
    )
    variants = ProductVariant.objects.filter(
        Exists(stocks.filter(product_variant_id=OuterRef("pk")))
    ).values("product_id")

    if stock_availability == StockAvailability.IN_STOCK:
        qs = qs.filter(Exists(variants.filter(product_id=OuterRef("pk"))))
    if stock_availability == StockAvailability.OUT_OF_STOCK:
        qs = qs.filter(~Exists(variants.filter(product_id=OuterRef("pk"))))
    return qs


def _filter_attributes(qs, _, value):
    if value:
        value_list = []
        boolean_list = []
        value_range_list = []
        date_range_list = []
        date_time_range_list = []

        for v in value:
            slug = v["slug"]
            if "values" in v:
                value_list.append((slug, v["values"]))
            elif "values_range" in v:
                value_range_list.append((slug, v["values_range"]))
            elif "date" in v:
                date_range_list.append((slug, v["date"]))
            elif "date_time" in v:
                date_time_range_list.append((slug, v["date_time"]))
            elif "boolean" in v:
                boolean_list.append((slug, v["boolean"]))

        qs = filter_products_by_attributes(
            qs,
            value_list,
            value_range_list,
            boolean_list,
            date_range_list,
            date_time_range_list,
        )
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
        ProductVariant.objects.filter(is_preorder=True)
        .filter(
            Q(preorder_end_date__isnull=True) | Q(preorder_end_date__gt=timezone.now())
        )
        .values("product_id")
    )
    if value:
        return qs.filter(Exists(variants.filter(product_id=OuterRef("pk"))))
    else:
        return qs.filter(~Exists(variants.filter(product_id=OuterRef("pk"))))


def filter_collections(qs, _, value):
    if value:
        _, collection_pks = resolve_global_ids_to_primary_keys(
            value, product_types.Collection
        )
        qs = filter_products_by_collections(qs, collection_pks)
    return qs


def _filter_products_is_published(qs, _, value, channel_slug):
    channel = Channel.objects.filter(slug=channel_slug).values("pk")
    product_channel_listings = ProductChannelListing.objects.filter(
        Exists(channel.filter(pk=OuterRef("channel_id"))), is_published=value
    ).values("product_id")

    # Filter out product for which there is no variant with price
    variant_channel_listings = ProductVariantChannelListing.objects.filter(
        Exists(channel.filter(pk=OuterRef("channel_id"))),
        price_amount__isnull=False,
    ).values("id")
    variants = ProductVariant.objects.filter(
        Exists(variant_channel_listings.filter(variant_id=OuterRef("pk")))
    ).values("product_id")

    return qs.filter(
        Exists(product_channel_listings.filter(product_id=OuterRef("pk"))),
        Exists(variants.filter(product_id=OuterRef("pk"))),
    )


def _filter_variant_price(qs, _, value, channel_slug):
    qs = filter_products_by_variant_price(
        qs, channel_slug, price_lte=value.get("lte"), price_gte=value.get("gte")
    )
    return qs


def _filter_minimal_price(qs, _, value, channel_slug):
    qs = filter_products_by_minimal_price(
        qs,
        channel_slug,
        minimal_price_lte=value.get("lte"),
        minimal_price_gte=value.get("gte"),
    )
    return qs


def _filter_stock_availability(qs, _, value, channel_slug):
    if value:
        qs = filter_products_by_stock_availability(qs, value, channel_slug)
    return qs


def filter_search(qs, _, value):
    return search_products(qs, value)


def _filter_collections_is_published(qs, _, value, channel_slug):
    return qs.filter(
        channel_listings__is_published=value,
        channel_listings__channel__slug=channel_slug,
    )


def filter_gift_card(qs, _, value):
    product_types = ProductType.objects.filter(kind=ProductTypeKind.GIFT_CARD)
    lookup = Exists(product_types.filter(id=OuterRef("product_type_id")))
    return qs.filter(lookup) if value is True else qs.exclude(lookup)


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


def filter_product_type_kind(qs, _, value):
    if value:
        qs = qs.filter(kind=value)
    return qs


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
        warehouses = Warehouse.objects.filter(pk__in=warehouse_pks).values("pk")
        variant_ids = Stock.objects.filter(
            Exists(warehouses.filter(pk=OuterRef("warehouse")))
        ).values("product_variant_id")
        variants = ProductVariant.objects.filter(id__in=variant_ids).values("pk")
        return qs.filter(Exists(variants.filter(product=OuterRef("pk"))))
    return qs


def filter_sku_list(qs, _, value):
    return qs.filter(sku__in=value)


def filter_is_preorder(qs, _, value):
    if value:
        return qs.filter(is_preorder=True).filter(
            Q(preorder_end_date__isnull=True) | Q(preorder_end_date__gte=timezone.now())
        )
    return qs.filter(
        Q(is_preorder=False)
        | (Q(is_preorder=True)) & Q(preorder_end_date__lt=timezone.now())
    )


def filter_quantity(qs, quantity_value, warehouse_ids=None):
    """Filter products queryset by product variants quantity.

    Return product queryset which contains at least one variant with aggregated quantity
    between given range. If warehouses is given, it aggregates quantity only
    from stocks which are in given warehouses.
    """
    stocks = Stock.objects.all()
    if warehouse_ids:
        _, warehouse_pks = resolve_global_ids_to_primary_keys(
            warehouse_ids, warehouse_types.Warehouse
        )
        stocks = stocks.filter(warehouse_id__in=warehouse_pks)
    stocks = stocks.values("product_variant_id").filter(
        product_variant_id=OuterRef("pk")
    )

    stocks = Subquery(stocks.values_list(Sum("quantity")))
    variants = ProductVariant.objects.annotate(
        total_quantity=ExpressionWrapper(stocks, output_field=IntegerField())
    )
    variants = list(
        filter_range_field(variants, "total_quantity", quantity_value).values_list(
            "product_id", flat=True
        )
    )
    return qs.filter(pk__in=variants)


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "updated_at", value)


class ProductStockFilterInput(graphene.InputObjectType):
    warehouse_ids = NonNullList(graphene.ID, required=False)
    quantity = graphene.Field(IntRangeInput, required=False)


class ProductFilter(MetadataFilterBase):
    is_published = django_filters.BooleanFilter(method="filter_is_published")
    collections = GlobalIDMultipleChoiceFilter(method=filter_collections)
    categories = GlobalIDMultipleChoiceFilter(method=filter_categories)
    has_category = django_filters.BooleanFilter(method=filter_has_category)
    price = ObjectTypeFilter(input_class=PriceRangeInput, method="filter_variant_price")
    minimal_price = ObjectTypeFilter(
        input_class=PriceRangeInput,
        method="filter_minimal_price",
        field_name="minimal_price_amount",
        help_text="Filter by the lowest variant price after discounts.",
    )
    attributes = ListObjectTypeFilter(
        input_class="saleor.graphql.attribute.types.AttributeInput",
        method="filter_attributes",
    )
    stock_availability = EnumFilter(
        input_class=StockAvailability,
        method="filter_stock_availability",
        help_text="Filter by variants having specific stock status.",
    )
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput,
        method=filter_updated_at_range,
        help_text="Filter by when was the most recent update.",
    )
    product_types = GlobalIDMultipleChoiceFilter(method=filter_product_types)
    stocks = ObjectTypeFilter(input_class=ProductStockFilterInput, method=filter_stocks)
    search = django_filters.CharFilter(method=filter_search)
    gift_card = django_filters.BooleanFilter(
        method=filter_gift_card,
        help_text="Filter on whether product is a gift card or not.",
    )
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id("Product"))
    has_preordered_variants = django_filters.BooleanFilter(
        method=filter_has_preordered_variants
    )

    class Meta:
        model = Product
        fields = [
            "is_published",
            "collections",
            "categories",
            "has_category",
            "attributes",
            "stock_availability",
            "stocks",
            "search",
        ]

    def filter_attributes(self, queryset, name, value):
        return _filter_attributes(queryset, name, value)

    def filter_variant_price(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return _filter_variant_price(queryset, name, value, channel_slug)

    def filter_minimal_price(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return _filter_minimal_price(queryset, name, value, channel_slug)

    def filter_is_published(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return _filter_products_is_published(
            queryset,
            name,
            value,
            channel_slug,
        )

    def filter_stock_availability(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return _filter_stock_availability(queryset, name, value, channel_slug)


class ProductVariantFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method="product_variant_filter_search")
    sku = ListObjectTypeFilter(input_class=graphene.String, method=filter_sku_list)
    is_preorder = django_filters.BooleanFilter(method=filter_is_preorder)
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_updated_at_range
    )

    class Meta:
        model = ProductVariant
        fields = ["search", "sku"]

    def product_variant_filter_search(self, queryset, _name, value):
        if not value:
            return queryset
        qs = Q(name__ilike=value) | Q(sku__ilike=value)
        products = Product.objects.filter(name__ilike=value).values("pk")
        qs |= Q(Exists(products.filter(variants=OuterRef("pk"))))
        return queryset.filter(qs)


class CollectionFilter(MetadataFilterBase):
    published = EnumFilter(
        input_class=CollectionPublished, method="filter_is_published"
    )
    search = django_filters.CharFilter(method="collection_filter_search")
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = Collection
        fields = ["published", "search"]

    def collection_filter_search(self, queryset, _name, value):
        if not value:
            return queryset
        name_slug_qs = Q(name__ilike=value) | Q(slug__ilike=value)
        return queryset.filter(name_slug_qs)

    def filter_is_published(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        if value == CollectionPublished.PUBLISHED:
            return _filter_collections_is_published(queryset, name, True, channel_slug)
        elif value == CollectionPublished.HIDDEN:
            return _filter_collections_is_published(queryset, name, False, channel_slug)
        return queryset


class CategoryFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method="category_filter_search")
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = Category
        fields = ["search"]

    @classmethod
    def category_filter_search(cls, queryset, _name, value):
        if not value:
            return queryset
        name_slug_desc_qs = (
            Q(name__ilike=value)
            | Q(slug__ilike=value)
            | Q(description_plaintext__ilike=value)
        )

        return queryset.filter(name_slug_desc_qs)


class ProductTypeFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method="filter_product_type_searchable")

    configurable = EnumFilter(
        input_class=ProductTypeConfigurable, method=filter_product_type_configurable
    )

    product_type = EnumFilter(input_class=ProductTypeEnum, method=filter_product_type)
    kind = EnumFilter(input_class=ProductTypeKindEnum, method=filter_product_type_kind)
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = ProductType
        fields = ["search", "configurable", "product_type"]

    @classmethod
    def filter_product_type_searchable(cls, queryset, _name, value):
        if not value:
            return queryset
        name_slug_qs = Q(name__ilike=value) | Q(slug__ilike=value)
        return queryset.filter(name_slug_qs)


class ProductFilterInput(ChannelFilterInputObjectType):
    class Meta:
        filterset_class = ProductFilter


class ProductVariantFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductVariantFilter


class CollectionFilterInput(ChannelFilterInputObjectType):
    class Meta:
        filterset_class = CollectionFilter


class CategoryFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CategoryFilter


class ProductTypeFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductTypeFilter
