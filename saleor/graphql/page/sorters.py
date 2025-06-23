from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.types import BaseEnum, SortInputObjectType


class PageSortField(BaseEnum):
    TITLE = ["title", "slug"]
    SLUG = ["slug"]
    VISIBILITY = ["is_published", "title", "slug"]
    CREATION_DATE = ["created_at", "title", "slug", "pk"]
    PUBLICATION_DATE = ["published_at", "title", "slug", "pk"]
    PUBLISHED_AT = ["published_at", "title", "slug"]
    CREATED_AT = ["created_at", "title", "slug"]

    class Meta:
        doc_category = DOC_CATEGORY_PAGES

    @property
    def description(self):
        descriptions = {
            PageSortField.TITLE.name: "title.",  # type: ignore[attr-defined] # noqa: E501
            PageSortField.SLUG.name: "slug.",  # type: ignore[attr-defined] # noqa: E501
            PageSortField.VISIBILITY.name: "visibility.",  # type: ignore[attr-defined] # noqa: E501
            PageSortField.CREATION_DATE.name: "creation date.",  # type: ignore[attr-defined] # noqa: E501
            PageSortField.CREATED_AT.name: "creation date.",  # type: ignore[attr-defined] # noqa: E501
            PageSortField.PUBLICATION_DATE.name: "publication date.",  # type: ignore[attr-defined] # noqa: E501
            PageSortField.PUBLISHED_AT.name: "publication date.",  # type: ignore[attr-defined] # noqa: E501
        }
        if self.name in descriptions:
            return f"Sort pages by {descriptions[self.name]}"
        raise ValueError(f"Unsupported enum value: {self.value}")

    @property
    def deprecation_reason(self):
        deprecations = {
            PageSortField.PUBLICATION_DATE.name: "Use `PUBLISHED_AT` instead.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            PageSortField.CREATION_DATE.name: "Use `CREATED_AT` instead.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in deprecations:
            return deprecations[self.name]
        return None


class PageSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        sort_enum = PageSortField
        type_name = "pages"


class PageTypeSortField(BaseEnum):
    NAME = ["name", "slug"]
    SLUG = ["slug"]

    class Meta:
        doc_category = DOC_CATEGORY_PAGES

    @property
    def description(self):
        if self.name in PageTypeSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort page types by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class PageTypeSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        sort_enum = PageTypeSortField
        type_name = "page types"
