import graphene
import graphql_jwt
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import staff_member_required

from ...graphql.core.filters import DistinctFilterSet
from ...graphql.page.types import Page
from ...graphql.product.types import ProductAttribute
from ...graphql.utils import get_node
from .page.mutations import PageCreate, PageDelete, PageUpdate
from .page.types import resolve_all_pages
from .product.types import resolve_attributes


class Query(graphene.ObjectType):
    attributes = DjangoFilterConnectionField(
        ProductAttribute, filterset_class=DistinctFilterSet,
        description='List of the shop\'s product attributes.')
    page = graphene.Field(
        Page, id=graphene.Argument(graphene.ID),
        description='Lookup a page by ID.')
    pages = DjangoFilterConnectionField(
        Page, filterset_class=DistinctFilterSet,
        description='List of shop\'s pages.')
    node = graphene.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')

    @staff_member_required
    def resolve_attributes(self, info):
        return resolve_attributes()

    @staff_member_required
    def resolve_page(self, info, id):
        return get_node(info, id, only_type=Page)

    @staff_member_required
    def resolve_pages(self, info):
        return resolve_all_pages()



class Mutations(graphene.ObjectType):
    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_update = PageUpdate.Field()

    token_create = graphql_jwt.ObtainJSONWebToken.Field()
    token_refresh = graphql_jwt.Refresh.Field()


schema = graphene.Schema(Query, Mutations)
