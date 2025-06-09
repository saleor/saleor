import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from saleor.product.models import ProductBrowsingHistory as ProductBrowsingHistoryModel
from saleor.graphql.core.connection import CountableConnection
from saleor.graphql.core.scalars import DateTime


class ProductBrowsingHistory(DjangoObjectType):
    class Meta:
        model = ProductBrowsingHistoryModel
        interfaces = [relay.Node]
        fields = ["id", "product", "user", "updated_at"]

    viewed_at = DateTime(source="created_at")


class ProductBrowsingHistoryConnection(CountableConnection):
    class Meta:
        node = ProductBrowsingHistory