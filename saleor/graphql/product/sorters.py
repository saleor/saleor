import graphene
from django.db.models import Count, QuerySet

from ...product.models import Category, Product
from ..core.enums import OrderDirection
from ..core.types import SortInputObjectType


class AttributeSortField(graphene.Enum):
    NAME = "name"
    SLUG = "slug"
    VALUE_REQUIRED = "value_required"
    IS_VARIANT_ONLY = "is_variant_only"
    VISIBLE_IN_STOREFRONT = "visible_in_storefront"
    FILTERABLE_IN_STOREFRONT = "filterable_in_storefront"
    FILTERABLE_IN_DASHBOARD = "filterable_in_dashboard"

    DASHBOARD_VARIANT_POSITION = "dashboard_variant_position"
    DASHBOARD_PRODUCT_POSITION = "dashboard_product_position"
    STOREFRONT_SEARCH_POSITION = "storefront_search_position"
    AVAILABLE_IN_GRID = "available_in_grid"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            AttributeSortField.NAME.name: "name",
            AttributeSortField.SLUG.name: "slug",
            AttributeSortField.VALUE_REQUIRED.name: "the value required flag",
            AttributeSortField.IS_VARIANT_ONLY.name: "the variant only flag",
            AttributeSortField.VISIBLE_IN_STOREFRONT.name: (
                "visibility in the storefront"
            ),
            AttributeSortField.FILTERABLE_IN_STOREFRONT.name: (
                "the filterable in storefront flag"
            ),
            AttributeSortField.FILTERABLE_IN_DASHBOARD.name: (
                "the filterable in dashboard flag"
            ),
            AttributeSortField.STOREFRONT_SEARCH_POSITION.name: (
                "their position in storefront"
            ),
        }
        if self.name in descriptions:
            return f"Sort attributes by {descriptions[self.name]}."
        if self == AttributeSortField.DASHBOARD_VARIANT_POSITION:
            return "Sort variant attributes by their position in dashboard."
        if self == AttributeSortField.DASHBOARD_PRODUCT_POSITION:
            return "Sort product attributes by their position in dashboard."
        if self == AttributeSortField.AVAILABLE_IN_GRID:
            return (
                "Sort attributes based on whether they can be displayed "
                "or not in a product grid."
            )
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def sort_by_dashboard_variant_position(
        queryset: QuerySet, sort_by: SortInputObjectType
    ) -> QuerySet:
        # pylint: disable=no-member
        is_asc = sort_by["direction"] == OrderDirection.ASC.value
        return queryset.variant_attributes_sorted(is_asc)

    @staticmethod
    def sort_by_dashboard_product_position(
        queryset: QuerySet, sort_by: SortInputObjectType
    ) -> QuerySet:
        # pylint: disable=no-member
        is_asc = sort_by["direction"] == OrderDirection.ASC.value
        return queryset.product_attributes_sorted(is_asc)


class AttributeSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = AttributeSortField
        type_name = "attributes"


class CategorySortField(graphene.Enum):
    NAME = "name"
    PRODUCT_COUNT = "product_count"
    SUBCATEGORY_COUNT = "subcategory_count"

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
    def sort_by_product_count(
        queryset: QuerySet, sort_by: SortInputObjectType
    ) -> QuerySet:
        return Category.tree.add_related_count(
            queryset, Product, "category", "product_count", cumulative=True
        ).order_by(f"{sort_by.direction}product_count")

    @staticmethod
    def sort_by_subcategory_count(
        queryset: QuerySet, sort_by: SortInputObjectType
    ) -> QuerySet:
        return queryset.annotate(subcategory_count=Count("children__id")).order_by(
            f"{sort_by.direction}subcategory_count", "pk"
        )


class CategorySortingInput(SortInputObjectType):
    class Meta:
        sort_enum = CategorySortField
        type_name = "categories"


class CollectionSortField(graphene.Enum):
    NAME = "name"
    AVAILABILITY = "is_published"
    PRODUCT_COUNT = "product_count"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            CollectionSortField.NAME,
            CollectionSortField.AVAILABILITY,
            CollectionSortField.PRODUCT_COUNT,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort collections by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def sort_by_product_count(
        queryset: QuerySet, sort_by: SortInputObjectType
    ) -> QuerySet:
        return queryset.annotate(product_count=Count("collectionproduct__id")).order_by(
            f"{sort_by.direction}product_count", "slug"
        )


class CollectionSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = CollectionSortField
        type_name = "collections"


class ProductOrderField(graphene.Enum):
    NAME = "name"
    PRICE = "price_amount"
    MINIMAL_PRICE = "minimal_variant_price_amount"
    DATE = "updated_at"
    TYPE = "product_type__name"
    PUBLISHED = "is_published"

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
        }
        if self.name in descriptions:
            return f"Sort products by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class ProductOrder(SortInputObjectType):
    attribute_id = graphene.Argument(
        graphene.ID,
        description=(
            "Sort product by the selected attribute's values.\n"
            "Note: this doesn't take translations into account yet."
        ),
    )

    class Meta:
        sort_enum = ProductOrderField
        type_name = "products"
