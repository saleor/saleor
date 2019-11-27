import graphene
from django.db.models import Count, QuerySet

from ..core.types import SortInputObjectType


class CollectionSortEnum(graphene.Enum):
    NAME = "name"
    AVAILABILITY = "is_published"
    PRODUCT_COUNT = "product_count"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            CollectionSortEnum.NAME,
            CollectionSortEnum.AVAILABILITY,
            CollectionSortEnum.PRODUCT_COUNT,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort collections by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def sort_by_product_count(queryset: QuerySet, sort_by: dict):
        return queryset.annotate(product_count=Count("collectionproduct__id")).order_by(
            f"{sort_by.direction}product_count", "slug"
        )


class CollectionSortInput(SortInputObjectType):
    class Meta:
        sort_enum = CollectionSortEnum
        type_name = "collection"
