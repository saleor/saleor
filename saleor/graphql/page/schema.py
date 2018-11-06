import graphene

from ..core.fields import PrefetchingConnectionField
from ..descriptions import DESCRIPTIONS
from .mutations import PageCreate, PageDelete, PageUpdate
from .resolvers import resolve_page, resolve_pages
from .types import Page


class PageQueries(graphene.ObjectType):
    page = graphene.Field(
        Page, id=graphene.Argument(graphene.ID), slug=graphene.String(),
        description='Lookup a page by ID or by slug.')
    pages = PrefetchingConnectionField(
        Page, query=graphene.String(
            description=DESCRIPTIONS['page']),
        description='List of the shop\'s pages.')

    def resolve_page(self, info, id=None, slug=None):
        return resolve_page(info, id, slug)

    def resolve_pages(self, info, query=None, **kwargs):
        return resolve_pages(info, query=query)


class PageMutations(graphene.ObjectType):
    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_update = PageUpdate.Field()
