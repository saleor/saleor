import graphene

from ..core.types import SortInputObjectType


class PageSortField(graphene.Enum):
    TITLE = ["title", "slug"]
    SLUG = ["slug"]
    VISIBILITY = ["is_published", "title", "slug"]
    CREATION_DATE = ["created", "title", "slug"]
    PUBLICATION_DATE = ["publication_date", "title", "slug"]

    @property
    def description(self):
        if self.name in PageSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort pages by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class PageSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = PageSortField
        type_name = "pages"


class PageTypeSortField(graphene.Enum):
    NAME = ["name", "slug"]
    SLUG = ["slug"]

    @property
    def description(self):
        if self.name in PageTypeSortField.__enum__._member_names_:
            sport_name = self.name.lower().replace("_", " ")
            return f"Sort page types by {sport_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class PageTypeSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = PageTypeSortField
        type_name = "page types"
