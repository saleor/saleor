import graphene
from django.db.models import Count, IntegerField, Min, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce

from ...product.models import Category, Product
from ..core.types import SortInputObjectType


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
    def qs_with_product_count(queryset: QuerySet) -> QuerySet:
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
    def qs_with_subcategory_count(queryset: QuerySet) -> QuerySet:
        return queryset.annotate(subcategory_count=Count("children__id"))


class CategorySortingInput(SortInputObjectType):
    class Meta:
        sort_enum = CategorySortField
        type_name = "categories"


class CollectionSortField(graphene.Enum):
    NAME = ["name"]
    AVAILABILITY = ["is_published", "name"]
    PRODUCT_COUNT = ["product_count", "name"]
    PUBLICATION_DATE = ["publication_date", "name"]

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            CollectionSortField.NAME,
            CollectionSortField.AVAILABILITY,
            CollectionSortField.PRODUCT_COUNT,
            CollectionSortField.PUBLICATION_DATE,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort collections by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_product_count(queryset: QuerySet) -> QuerySet:
        return queryset.annotate(product_count=Count("collectionproduct__id"))


class CollectionSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = CollectionSortField
        type_name = "collections"


class ProductOrderField(graphene.Enum):
    NAME = ["name", "slug"]
    PRICE = ["min_variants_price_amount", "name", "slug"]
    MINIMAL_PRICE = ["minimal_variant_price_amount", "name", "slug"]
    DATE = ["updated_at", "name", "slug"]
    TYPE = ["product_type__name", "name", "slug"]
    PUBLISHED = ["is_published", "name", "slug"]
    PUBLICATION_DATE = ["publication_date", "name", "slug"]

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            ProductOrderField.NAME.name: "name",
            ProductOrderField.PRICE.name: "price",
            ProductOrderField.TYPE.name: "type",
            ProductOrderField.MINIMAL_PRICE.name: (
                "a minimal price of a product's variant"
            ),
            ProductOrderField.DATE.name: "update date",
            ProductOrderField.PUBLISHED.name: "publication status",
            ProductOrderField.PUBLICATION_DATE.name: "publication date",
        }
        if self.name in descriptions:
            return f"Sort products by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_price(queryset: QuerySet) -> QuerySet:
        return queryset.annotate(
            min_variants_price_amount=Min("variants__price_amount")
        )


class ProductOrder(SortInputObjectType):
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
