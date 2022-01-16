import graphene


from saleor.graphql.core.connection import create_connection_slice , filter_connection_queryset

from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.core.utils import from_global_id_or_error

from ..models import CustomerGroup
from . import types
from .filters import GroupFilterInput
from .mutations import CustomerGroupCreate, CustomerGroupDelete, CustomerGroupUpdate


class CustomerGroupQueries(graphene.ObjectType):

    customer_group = graphene.Field(
        types.CustomerGroup,
        id=graphene.Argument(
            graphene.ID, description="ID of the customer group", required=True
        ),
        description="Look up a customer group by ID",
    )
    customer_groups = FilterConnectionField(
        types.CustomerGroupConnection,
        filter=GroupFilterInput(description="Filtering options for group."),
    )

    def resolve_customer_groups(root, info, **kwargs):
        # Querying a list
        qs = CustomerGroup.objects.all()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, types.CustomerGroupConnection)

    def resolve_customer_group(self, info, id, **data):
        # Querying a single CustomerGroup
        _, id = from_global_id_or_error(id, types.CustomerGroup)
        return CustomerGroup.objects.get(id=id)


class CustomerGroupMutations(graphene.ObjectType):
    customer_group_create = CustomerGroupCreate.Field()
    customer_group_update = CustomerGroupUpdate.Field()
    customer_group_delete = CustomerGroupDelete.Field()


schema = graphene.Schema(
    query=CustomerGroupQueries,
    mutation=CustomerGroupMutations,
    types=[types.CustomerGroup],
)
