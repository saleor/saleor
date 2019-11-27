import graphene

from ..core.types import SortInputObjectType


class CollectionSortEnum(graphene.Enum):
    NAME = "name"
    AVAILABILITY = "is_published"
    # TODO: Add sorting by product count
    # PRODUCT_COUNT = "collectionproduct"

    @property
    def description(self):
        if self in [
            CollectionSortEnum.NAME,
            CollectionSortEnum.AVAILABILITY,
            # CollectionSortEnum.PRODUCT_COUNT,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort collections by {sort_name}."
        # pylint: disable=no-member
        raise ValueError("Unsupported enum value: %s" % self.value)


class CollectionSortInput(SortInputObjectType):
    class Meta:
        sort_enum = CollectionSortEnum
        type_name = "collection"
