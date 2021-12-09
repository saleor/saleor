import graphene
from saleor.graphql.core.utils import from_global_id_or_error
from saleor.plugins.customer_group.graphql.types import CustomerGroupType

from saleor.plugins.customer_group.models import CustomerGroup

from .mutations import (
    CustomerGroupActivate,
    CustomerGroupCreate,
    CustomerGroupDeactivate,
)


class CustomerGroupQueries(graphene.ObjectType):
    customer_group = graphene.Field(
        CustomerGroupType,
        id=graphene.ID(description="ID of the CustomerGroup", required=True),
        description="Look up a CustomerGroup by ID",
    )
    customer_groups = graphene.List(
        graphene.NonNull(CustomerGroupType), description="List of all CustomerGroups"
    )

    def resolve_customer_groups(root, info, **kwargs):
        # Querying a list
        return CustomerGroup.objects.all()

    def resolve_customer_group(root, info, id):
        # Querying a single CustomerGroup
        _, id = from_global_id_or_error(id, CustomerGroupType)
        return CustomerGroup.objects.get(id=id)


class CustomerGroupMutations(graphene.ObjectType):
    customer_group_create = CustomerGroupCreate.Field()
    customer_group_activate = CustomerGroupActivate.Field()
    customer_group_deactivate = CustomerGroupDeactivate.Field()


schema = graphene.Schema(query=CustomerGroupQueries, mutation=CustomerGroupMutations)
