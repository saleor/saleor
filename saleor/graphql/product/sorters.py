import graphene
from django.db.models import (
    BooleanField,
    Count,
    DateTimeField,
    ExpressionWrapper,
    F,
    IntegerField,
    Min,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
)
from django.db.models.expressions import Window
from django.db.models.functions import Coalesce, DenseRank

from ...product.models import (
    Category,
    CollectionChannelListing,
    Product,
    ProductChannelListing,
)
from ..core.descriptions import CHANNEL_REQUIRED, DEPRECATED_IN_3X_INPUT
from ..core.types import ChannelSortInputObjectType, SortInputObjectType


class CategorySortField(graphene.Enum):
    NAME = ["name", "slug"]
    PRODUCT_COUNT = ["product_count", "name", "slug"]
    SUBCATEGORY_COUNT = ["subcategory_count", "name", "slug"]

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            CategorySortField.NAME,
            CategorySortField.PRODUCT_COUNT,
            CategorySortField.SUBCATEGORY_COUNT,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort categories by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_product_count(queryset: QuerySet, **_kwargs) -> QuerySet:
        return queryset.annotate(
            product_count=Coalesce(
                Subquery(
                    Category.tree.add_related_count(
                        queryset, Product, "category", "p_c", cumulative=True
                    )
                    .values("p_c")
                    .filter(pk=OuterRef("pk"))[:1]
                ),
                0,
                output_field=IntegerField(),
            )
        )

    @staticmethod
    def qs_with_subcategory_count(queryset: QuerySet, **_kwargs) -> QuerySet:
        return queryset.annotate(subcategory_count=Count("children__id"))


class CategorySortingInput(ChannelSortInputObjectType):
    class Meta:
        sort_enum = CategorySortField
        type_name = "categories"


class CollectionSortField(graphene.Enum):
    NAME = ["name", "slug"]
    AVAILABILITY = ["is_published", "slug"]
    PRODUCT_COUNT = ["product_count", "slug"]
    PUBLICATION_DATE = ["published_at", "slug"]
    PUBLISHED_AT = ["published_at", "slug"]

    @property
    def description(self):
        descrption_extras = {
            CollectionSortField.AVAILABILITY.name: [CHANNEL_REQUIRED],
            CollectionSortField.PUBLICATION_DATE.name: [
                CHANNEL_REQUIRED,
                DEPRECATED_IN_3X_INPUT,
            ],
            CollectionSortField.PUBLISHED_AT.name: [CHANNEL_REQUIRED],
        }
        if self.name in CollectionSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            description = f"Sort collections by {sort_name}."
            if extras := descrption_extras.get(self.name):
                description += "".join(extras)
            return description
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_product_count(queryset: QuerySet, **_kwargs) -> QuerySet:
        return queryset.annotate(product_count=Count("collectionproduct__id"))

    @staticmethod
    def qs_with_availability(queryset: QuerySet, channel_slug: str) -> QuerySet:
        subquery = Subquery(
            CollectionChannelListing.objects.filter(
                collection_id=OuterRef("pk"), channel__slug=str(channel_slug)
            ).values_list("is_published")[:1]
        )
        return queryset.annotate(
            is_published=ExpressionWrapper(subquery, output_field=BooleanField())
        )

    @staticmethod
    def qs_with_publication_date(queryset: QuerySet, channel_slug: str) -> QuerySet:
        return CollectionSortField.qs_with_published_at(queryset, channel_slug)

    @staticmethod
    def qs_with_published_at(queryset: QuerySet, channel_slug: str) -> QuerySet:
        subquery = Subquery(
            CollectionChannelListing.objects.filter(
                collection_id=OuterRef("pk"), channel__slug=str(channel_slug)
            ).values_list("published_at")[:1]
        )
        return queryset.annotate(
            published_at=ExpressionWrapper(subquery, output_field=DateTimeField())
        )


class CollectionSortingInput(ChannelSortInputObjectType):
    class Meta:
        sort_enum = CollectionSortField
        type_name = "collections"


class ProductOrderField(graphene.Enum):
    NAME = ["name", "slug"]
    RANK = ["search_rank", "id"]
    PRICE = ["min_variants_price_amount", "name", "slug"]
    MINIMAL_PRICE = ["discounted_price_amount", "name", "slug"]
    LAST_MODIFIED = ["updated_at", "name", "slug"]
    DATE = ["updated_at", "name", "slug"]
    TYPE = ["product_type__name", "name", "slug"]
    PUBLISHED = ["is_published", "name", "slug"]
    PUBLICATION_DATE = ["published_at", "name", "slug"]
    PUBLISHED_AT = ["published_at", "name", "slug"]
    LAST_MODIFIED_AT = ["updated_at", "name", "slug"]
    COLLECTION = ["collectionproduct__sort_order", "pk"]
    RATING = ["rating", "name", "slug"]

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            ProductOrderField.COLLECTION.name: (
                "collection. Note: "
                "This option is available only for the `Collection.products` query."
                + CHANNEL_REQUIRED
            ),
            ProductOrderField.RANK.name: (
                "rank. Note: This option is available only with the `search` filter."
            ),
            ProductOrderField.NAME.name: "name.",
            ProductOrderField.PRICE.name: ("price." + CHANNEL_REQUIRED),
            ProductOrderField.TYPE.name: "type.",
            ProductOrderField.MINIMAL_PRICE.name: (
                "a minimal price of a product's variant." + CHANNEL_REQUIRED
            ),
            ProductOrderField.DATE.name: f"update date. {DEPRECATED_IN_3X_INPUT}",
            ProductOrderField.PUBLISHED.name: (
                "publication status." + CHANNEL_REQUIRED
            ),
            ProductOrderField.PUBLICATION_DATE.name: (
                "publication date." + CHANNEL_REQUIRED + DEPRECATED_IN_3X_INPUT
            ),
            ProductOrderField.LAST_MODIFIED.name: (
                f"update date. {DEPRECATED_IN_3X_INPUT}"
            ),
            ProductOrderField.PUBLISHED_AT.name: (
                "publication date." + CHANNEL_REQUIRED
            ),
            ProductOrderField.LAST_MODIFIED_AT.name: "update date.",
            ProductOrderField.RATING.name: "rating.",
        }
        if self.name in descriptions:
            return f"Sort products by {descriptions[self.name]}"
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_price(queryset: QuerySet, channel_slug: str) -> QuerySet:
        return queryset.annotate(
            min_variants_price_amount=Min(
                "variants__channel_listings__price_amount",
                filter=Q(variants__channel_listings__channel__slug=str(channel_slug))
                & Q(variants__channel_listings__price_amount__isnull=False),
            )
        )

    @staticmethod
    def qs_with_minimal_price(queryset: QuerySet, channel_slug: str) -> QuerySet:
        return queryset.annotate(
            discounted_price_amount=Min(
                "channel_listings__discounted_price_amount",
                filter=Q(channel_listings__channel__slug=str(channel_slug)),
            )
        )

    @staticmethod
    def qs_with_published(queryset: QuerySet, channel_slug: str) -> QuerySet:
        subquery = Subquery(
            ProductChannelListing.objects.filter(
                product_id=OuterRef("pk"), channel__slug=str(channel_slug)
            ).values_list("is_published")[:1]
        )
        return queryset.annotate(
            is_published=ExpressionWrapper(subquery, output_field=BooleanField())
        )

    @staticmethod
    def qs_with_publication_date(queryset: QuerySet, channel_slug: str) -> QuerySet:
        return ProductOrderField.qs_with_published_at(queryset, channel_slug)

    @staticmethod
    def qs_with_published_at(queryset: QuerySet, channel_slug: str) -> QuerySet:
        subquery = Subquery(
            ProductChannelListing.objects.filter(
                product_id=OuterRef("pk"), channel__slug=str(channel_slug)
            ).values_list("published_at")[:1]
        )
        return queryset.annotate(
            published_at=ExpressionWrapper(subquery, output_field=DateTimeField())
        )

    @staticmethod
    def qs_with_collection(queryset: QuerySet, **_kwargs) -> QuerySet:
        return queryset.annotate(
            sort_order=Window(
                expression=DenseRank(),
                order_by=(
                    F("collectionproduct__sort_order").asc(nulls_last=True),
                    F("collectionproduct__id"),
                ),
            )
        )


class ProductOrder(ChannelSortInputObjectType):
    attribute_id = graphene.Argument(
        graphene.ID,
        description=(
            "Sort product by the selected attribute's values.\n"
            "Note: this doesn't take translations into account yet."
        ),
    )
    field = graphene.Argument(
        ProductOrderField, description="Sort products by the selected field."
    )

    class Meta:
        sort_enum = ProductOrderField


class ProductVariantSortField(graphene.Enum):
    LAST_MODIFIED_AT = ["updated_at", "name", "pk"]

    @property
    def description(self):
        # pylint: disable=no-member
        if self.name in ProductVariantSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort products variants by {sort_name}."

        raise ValueError("Unsupported enum value: %s" % self.value)


class ProductVariantSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ProductVariantSortField
        type_name = "productVariants"


class ProductTypeSortField(graphene.Enum):
    NAME = ["name", "slug"]
    DIGITAL = ["is_digital", "name", "slug"]
    SHIPPING_REQUIRED = ["is_shipping_required", "name", "slug"]

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            ProductTypeSortField.NAME.name: "name",
            ProductTypeSortField.DIGITAL.name: "type",
            ProductTypeSortField.SHIPPING_REQUIRED.name: "shipping",
        }
        if self.name in descriptions:
            return f"Sort products by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class ProductTypeSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ProductTypeSortField
        type_name = "product types"
