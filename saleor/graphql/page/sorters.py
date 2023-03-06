import graphene

from ..core.descriptions import ADDED_IN_38, DEPRECATED_IN_3X_INPUT
from ..core.types import SortInputObjectType


class PageSortField(graphene.Enum):
    TITLE = ["title", "slug"]
    SLUG = ["slug"]
    VISIBILITY = ["is_published", "title", "slug"]
    CREATION_DATE = ["created_at", "title", "slug"]
    PUBLICATION_DATE = ["published_at", "title", "slug"]
    PUBLISHED_AT = ["published_at", "title", "slug"]
    CREATED_AT = ["created_at", "title", "slug"]

    @property
    def description(self):
        if self.name in PageSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            description = f"Sort pages by {sort_name}."
            if self.name == "PUBLICATION_DATE":
                description += DEPRECATED_IN_3X_INPUT
            if self.name == "CREATION_DATE":
                description += DEPRECATED_IN_3X_INPUT
            if self.name == "CREATED_AT":
                description += ADDED_IN_38
            return description
        raise ValueError(f"Unsupported enum value: {self.value}")


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
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort page types by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class PageTypeSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = PageTypeSortField
        type_name = "page types"
