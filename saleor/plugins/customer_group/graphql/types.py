from graphene import relay
from graphene.types.objecttype import ObjectType
from graphene.types.scalars import String
from graphene_django import DjangoObjectType

from saleor.graphql.account.types import User
from saleor.plugins.customer_group.models import CustomerGroup


class CustomerGroupType(DjangoObjectType):
    class Meta:
        model = CustomerGroup
        fields = "__all__"


class Customer(ObjectType):
    class Meta:
        interfaces = [relay.Node]

    name = String()


class CustomerConnection(relay.Connection):
    class Meta:
        node = User
