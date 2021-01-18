import graphene

from ..core.fields import FilterInputConnectionField
from ..translations.mutations import PageTranslate
from .bulk_mutations import PageBulkDelete, PageBulkPublish, PageTypeBulkDelete
from .filters import PageFilterInput, PageTypeFilterInput
from .mutations.attributes import (
    PageAttributeAssign,
    PageAttributeUnassign,
    PageReorderAttributeValues,
    PageTypeReorderAttributes,
)
from .mutations.pages import (
    PageCreate,
    PageDelete,
    PageTypeCreate,
    PageTypeDelete,
    PageTypeUpdate,
    PageUpdate,
)
from .resolvers import (
    resolve_page,
    resolve_page_type,
    resolve_page_types,
    resolve_pages,
)
from .sorters import PageSortingInput, PageTypeSortingInput
from .types import Page, PageType


class PageQueries(graphene.ObjectType):
    page = graphene.Field(
        Page,
        id=graphene.Argument(graphene.ID, description="ID of the page."),
        slug=graphene.String(description="The slug of the page."),
        description="Look up a page by ID or slug.",
    )
    pages = FilterInputConnectionField(
        Page,
        sort_by=PageSortingInput(description="Sort pages."),
        filter=PageFilterInput(description="Filtering options for pages."),
        description="List of the shop's pages.",
    )
    page_type = graphene.Field(
        PageType,
        id=graphene.Argument(
            graphene.ID, description="ID of the page type.", required=True
        ),
        description="Look up a page type by ID.",
    )
    page_types = FilterInputConnectionField(
        PageType,
        sort_by=PageTypeSortingInput(description="Sort page types."),
        filter=PageTypeFilterInput(description="Filtering options for page types."),
        description="List of the page types.",
    )

    def resolve_page(self, info, id=None, slug=None):
        return resolve_page(info, id, slug)

    def resolve_pages(self, info, **kwargs):
        return resolve_pages(info, **kwargs)

    def resolve_page_type(self, info, id):
        return resolve_page_type(info, id)

    def resolve_page_types(self, info, **kwargs):
        return resolve_page_types(info, **kwargs)


class PageMutations(graphene.ObjectType):
    # page mutations
    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_bulk_delete = PageBulkDelete.Field()
    page_bulk_publish = PageBulkPublish.Field()
    page_update = PageUpdate.Field()
    page_translate = PageTranslate.Field()

    # page type mutations
    page_type_create = PageTypeCreate.Field()
    page_type_update = PageTypeUpdate.Field()
    page_type_delete = PageTypeDelete.Field()
    page_type_bulk_delete = PageTypeBulkDelete.Field()

    # attributes mutations
    page_attribute_assign = PageAttributeAssign.Field()
    page_attribute_unassign = PageAttributeUnassign.Field()
    page_type_reorder_attributes = PageTypeReorderAttributes.Field()
    page_reorder_attribute_values = PageReorderAttributeValues.Field()
