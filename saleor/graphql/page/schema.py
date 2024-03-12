import graphene

from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.fields import BaseField, FilterConnectionField
from ..core.utils import from_global_id_or_error
from ..translations.mutations import PageTranslate
from .bulk_mutations import PageBulkDelete, PageBulkPublish, PageTypeBulkDelete
from .filters import PageFilterInput, PageTypeFilterInput
from .mutations import (
    PageAttributeAssign,
    PageAttributeUnassign,
    PageCreate,
    PageDelete,
    PageReorderAttributeValues,
    PageTypeCreate,
    PageTypeDelete,
    PageTypeReorderAttributes,
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
from .types import Page, PageCountableConnection, PageType, PageTypeCountableConnection


class PageQueries(graphene.ObjectType):
    page = BaseField(
        Page,
        id=graphene.Argument(graphene.ID, description="ID of the page."),
        slug=graphene.String(description="The slug of the page."),
        description="Look up a page by ID or slug.",
        doc_category=DOC_CATEGORY_PAGES,
    )
    pages = FilterConnectionField(
        PageCountableConnection,
        sort_by=PageSortingInput(description="Sort pages."),
        filter=PageFilterInput(description="Filtering options for pages."),
        description="List of the shop's pages.",
        doc_category=DOC_CATEGORY_PAGES,
    )
    page_type = BaseField(
        PageType,
        id=graphene.Argument(
            graphene.ID, description="ID of the page type.", required=True
        ),
        description="Look up a page type by ID.",
        doc_category=DOC_CATEGORY_PAGES,
    )
    page_types = FilterConnectionField(
        PageTypeCountableConnection,
        sort_by=PageTypeSortingInput(description="Sort page types."),
        filter=PageTypeFilterInput(description="Filtering options for page types."),
        description="List of the page types.",
        doc_category=DOC_CATEGORY_PAGES,
    )

    @staticmethod
    def resolve_page(_root, info: ResolveInfo, *, id=None, slug=None):
        return resolve_page(info, id, slug)

    @staticmethod
    def resolve_pages(_root, info: ResolveInfo, **kwargs):
        qs = resolve_pages(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, PageCountableConnection)

    @staticmethod
    def resolve_page_type(_root, info: ResolveInfo, *, id):
        _, id = from_global_id_or_error(id, PageType)
        return resolve_page_type(info, id)

    @staticmethod
    def resolve_page_types(_root, info: ResolveInfo, **kwargs):
        qs = resolve_page_types(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, PageTypeCountableConnection)


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
