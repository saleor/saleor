import django_filters
import graphene
from django.db.models import Exists, OuterRef

from ....channel.models import Channel
from ....product.models import (
    CollectionProduct,
    Product,
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)
from ...channel.filters import get_channel_slug_from_filter_data
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.filters import (
    BooleanWhereFilter,
    ChannelFilterInputObjectType,
    EnumFilter,
    EnumWhereFilter,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeFilter,
    ListObjectTypeWhereFilter,
    MetadataFilterBase,
    MetadataWhereFilterBase,
    ObjectTypeFilter,
    ObjectTypeWhereFilter,
    OperationObjectTypeWhereFilter,
)
from ...core.filters.where_input import (
    DateTimeFilterInput,
    DecimalFilterInput,
    GlobalIDFilterInput,
    StringFilterInput,
    WhereInputObjectType,
)
from ...core.scalars import DateTime
from ...core.types import (
    BaseInputObjectType,
    DateTimeRangeInput,
    IntRangeInput,
    NonNullList,
    PriceRangeInput,
)
from ...utils.filters import (
    filter_by_id,
    filter_by_ids,
    filter_slug_list,
    filter_where_by_id_field,
    filter_where_by_numeric_field,
    filter_where_by_value_field,
)
from ..enums import StockAvailability
from .product_attributes import filter_products_by_attributes, validate_attribute_input
from .product_helpers import (
    filter_categories,
    filter_collections,
    filter_gift_card,
    filter_has_category,
    filter_has_preordered_variants,
    filter_minimal_price,
    filter_product_types,
    filter_products_channel_field_from_date,
    filter_products_is_available,
    filter_products_is_published,
    filter_products_visible_in_listing,
    filter_search,
    filter_stock_availability,
    filter_stocks,
    filter_variant_price,
    where_filter_by_categories,
    where_filter_gift_card,
    where_filter_has_category,
    where_filter_has_preordered_variants,
    where_filter_products_channel_field_from_date,
    where_filter_products_is_available,
    where_filter_stock_availability,
    where_filter_stocks,
    where_filter_updated_at_range,
)
from .shared import filter_updated_at_range

T_PRODUCT_FILTER_QUERIES = dict[int, list[int]]


class ProductStockFilterInput(BaseInputObjectType):
    warehouse_ids = NonNullList(graphene.ID, required=False)
    quantity = graphene.Field(IntRangeInput, required=False)

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductFilter(MetadataFilterBase):
    is_published = django_filters.BooleanFilter(method="filter_is_published")
    published_from = ObjectTypeFilter(
        input_class=DateTime,
        method="filter_published_from",
        help_text="Filter by the publication date.",
    )
    is_available = django_filters.BooleanFilter(
        method="filter_is_available",
        help_text="Filter by availability for purchase.",
    )
    available_from = ObjectTypeFilter(
        input_class=DateTime,
        method="filter_available_from",
        help_text="Filter by the date of availability for purchase.",
    )
    is_visible_in_listing = django_filters.BooleanFilter(
        method="filter_listed",
        help_text="Filter by visibility in product listings.",
    )
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
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

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
        if not value:
            return queryset
        return filter_products_by_attributes(queryset, value)

    def filter_variant_price(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_variant_price(queryset, name, value, channel_slug)

    def filter_minimal_price(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_minimal_price(queryset, name, value, channel_slug)

    def filter_is_published(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_products_is_published(
            queryset,
            name,
            value,
            channel_slug,
        )

    def filter_published_from(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_products_channel_field_from_date(
            queryset,
            name,
            value,
            channel_slug,
            "published_at",
        )

    def filter_is_available(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_products_is_available(
            queryset,
            name,
            value,
            channel_slug,
        )

    def filter_available_from(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_products_channel_field_from_date(
            queryset,
            name,
            value,
            channel_slug,
            "available_for_purchase_at",
        )

    def filter_listed(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_products_visible_in_listing(
            queryset,
            name,
            value,
            channel_slug,
        )

    def filter_stock_availability(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_stock_availability(queryset, name, value, channel_slug)

    def is_valid(self):
        if attributes := self.data.get("attributes"):
            validate_attribute_input(attributes, self.queryset.db)
        return super().is_valid()


class ProductWhere(MetadataWhereFilterBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Product"))
    name = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_product_name",
        help_text="Filter by product name.",
    )
    slug = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_product_slug",
        help_text="Filter by product slug.",
    )
    product_type = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method="filter_product_type",
        help_text="Filter by product type.",
    )
    category = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method="filter_category",
        help_text="Filter by product category.",
    )
    collection = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method="filter_collection",
        help_text="Filter by collection.",
    )
    is_available = BooleanWhereFilter(
        method="filter_is_available", help_text="Filter by availability for purchase."
    )
    is_published = BooleanWhereFilter(
        method="filter_is_published", help_text="Filter by public visibility."
    )
    is_visible_in_listing = BooleanWhereFilter(
        method="filter_is_listed", help_text="Filter by visibility on the channel."
    )
    published_from = ObjectTypeWhereFilter(
        input_class=DateTime,
        method="filter_published_from",
        help_text="Filter by the publication date.",
    )
    available_from = ObjectTypeWhereFilter(
        input_class=DateTime,
        method="filter_available_from",
        help_text="Filter by the date of availability for purchase.",
    )
    has_category = BooleanWhereFilter(
        method=where_filter_has_category,
        help_text="Filter by product with category assigned.",
    )
    price = OperationObjectTypeWhereFilter(
        input_class=DecimalFilterInput,
        method="filter_variant_price",
        help_text="Filter by product variant price.",
    )
    minimal_price = OperationObjectTypeWhereFilter(
        input_class=DecimalFilterInput,
        method="filter_minimal_price",
        field_name="minimal_price_amount",
        help_text="Filter by the lowest variant price after discounts.",
    )
    attributes = ListObjectTypeWhereFilter(
        input_class="saleor.graphql.attribute.types.AttributeInput",
        method="filter_attributes",
        help_text="Filter by attributes associated with the product.",
    )
    stock_availability = EnumWhereFilter(
        input_class=StockAvailability,
        method="filter_stock_availability",
        help_text="Filter by variants having specific stock status.",
    )
    stocks = ObjectTypeWhereFilter(
        input_class=ProductStockFilterInput,
        method=where_filter_stocks,
        help_text="Filter by stock of the product variant.",
    )
    gift_card = BooleanWhereFilter(
        method=where_filter_gift_card,
        help_text="Filter on whether product is a gift card or not.",
    )
    has_preordered_variants = BooleanWhereFilter(
        method=where_filter_has_preordered_variants,
        help_text="Filter by product with preordered variants.",
    )
    updated_at = ObjectTypeWhereFilter(
        input_class=DateTimeFilterInput,
        method=where_filter_updated_at_range,
        help_text="Filter by when was the most recent update.",
    )

    class Meta:
        model = Product
        fields = []

    @staticmethod
    def filter_product_name(qs, _, value):
        return filter_where_by_value_field(qs, "name", value)

    @staticmethod
    def filter_product_slug(qs, _, value):
        return filter_where_by_value_field(qs, "slug", value)

    @staticmethod
    def filter_product_type(qs, _, value):
        return filter_where_by_id_field(qs, "product_type", value, "ProductType")

    @staticmethod
    def filter_category(qs, _, value):
        return where_filter_by_categories(qs, value)

    @staticmethod
    def filter_collection(qs, _, value):
        collection_products_qs = CollectionProduct.objects.using(qs.db).filter()
        collection_products_qs = filter_where_by_id_field(
            collection_products_qs, "collection_id", value, "Collection"
        )
        collection_products = collection_products_qs.values("product_id")
        return qs.filter(Exists(collection_products.filter(product_id=OuterRef("pk"))))

    def filter_is_available(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return where_filter_products_is_available(
            queryset,
            name,
            value,
            channel_slug,
        )

    def filter_is_published(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_products_is_published(
            queryset,
            name,
            value,
            channel_slug,
        )

    def filter_is_listed(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_products_visible_in_listing(
            queryset,
            name,
            value,
            channel_slug,
        )

    def filter_published_from(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return where_filter_products_channel_field_from_date(
            queryset,
            name,
            value,
            channel_slug,
            "published_at",
        )

    def filter_available_from(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return where_filter_products_channel_field_from_date(
            queryset,
            name,
            value,
            channel_slug,
            "available_for_purchase_at",
        )

    def filter_variant_price(self, qs, _, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        channel_id = Channel.objects.using(qs.db).filter(slug=channel_slug).values("pk")
        variant_listing = ProductVariantChannelListing.objects.using(qs.db).filter(
            Exists(channel_id.filter(pk=OuterRef("channel_id")))
        )
        variant_listing = filter_where_by_numeric_field(
            variant_listing, "price_amount", value
        )
        variant_listing = variant_listing.values("variant_id")
        variants = (
            ProductVariant.objects.using(qs.db)
            .filter(Exists(variant_listing.filter(variant_id=OuterRef("pk"))))
            .values("product_id")
        )
        return qs.filter(Exists(variants.filter(product_id=OuterRef("pk"))))

    def filter_minimal_price(self, qs, _, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        channel = Channel.objects.using(qs.db).filter(slug=channel_slug).first()
        if not channel:
            return qs
        product_listing = ProductChannelListing.objects.using(qs.db).filter(
            channel_id=channel.id
        )
        product_listing = filter_where_by_numeric_field(
            product_listing, "discounted_price_amount", value
        )
        product_listing = product_listing.values("product_id")
        return qs.filter(Exists(product_listing.filter(product_id=OuterRef("pk"))))

    @staticmethod
    def filter_attributes(queryset, name, value):
        return filter_products_by_attributes(queryset, value)

    def filter_stock_availability(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return where_filter_stock_availability(queryset, name, value, channel_slug)

    def is_valid(self):
        if attributes := self.data.get("attributes"):
            validate_attribute_input(attributes, self.queryset.db)
        return super().is_valid()


class ProductFilterInput(ChannelFilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = ProductFilter


class ProductWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = ProductWhere
