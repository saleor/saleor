import graphene

from ..core.fields import FilterInputConnectionField
from ..translations.mutations import PageTranslate
from .bulk_mutations import PageBulkDelete, PageBulkPublish
from .filters import PageFilterInput
from .mutations import PageCreate, PageDelete, PageUpdate
from .resolvers import resolve_page, resolve_pages
from .sorters import PageSortingInput
from .types import Page


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

    def resolve_page(self, info, id=None, slug=None):
        return resolve_page(info, id, slug)

    def resolve_pages(self, info, **kwargs):
        return resolve_pages(info, **kwargs)


class PageMutations(graphene.ObjectType):
    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_bulk_delete = PageBulkDelete.Field()
    page_bulk_publish = PageBulkPublish.Field()
    page_update = PageUpdate.Field()
    page_translate = PageTranslate.Field()
