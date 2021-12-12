import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from saleor.graphql.core.utils import from_global_id_or_error
from saleor.plugins.customer_group.graphql.types import CustomerGroupType
from saleor.plugins.customer_group.models import CustomerGroup

from .mutations import (
    CustomerGroupActivate,
    CustomerGroupCreate,
    CustomerGroupDeactivate,
)


class CustomerGroupNode(DjangoObjectType):
    class Meta:
        model = CustomerGroup
        filter_fields = ["id", "name", "description", "customers"]
        interfaces = (graphene.relay.Node,)

    def resolve_customer_groups(root, info, **kwargs):
        # Querying a list
        return CustomerGroup.objects.all()

    def resolve_customer_group(self, info, **data):
        # Querying a single CustomerGroup
        _, id = from_global_id_or_error(data.get("id"), CustomerGroupType)
        return CustomerGroup.objects.get(id=id)


class CustomerGroupQueries(graphene.ObjectType):
    customer_group = graphene.relay.Node.Field(CustomerGroupNode)
    customer_groups = DjangoFilterConnectionField(CustomerGroupNode)


class CustomerGroupMutations(graphene.ObjectType):
    customer_group_create = CustomerGroupCreate.Field()
    customer_group_activate = CustomerGroupActivate.Field()
    customer_group_deactivate = CustomerGroupDeactivate.Field()


schema = graphene.Schema(query=CustomerGroupQueries, mutation=CustomerGroupMutations)
