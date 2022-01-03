import graphene

from saleor.plugins.customer_group.graphql.errors import CustomerGroupError

from ....graphql.core.mutations import ModelDeleteMutation, ModelMutation
from .. import models
from .custom_permissions import CustomerGroupPermissions


class CustomerGroupInput(graphene.InputObjectType):
    is_active = graphene.Boolean(
        description="isActive flag to enable or diable customer group from mustations"
    )
    description = graphene.String(description="description of the customer group.")
    customers = graphene.List(
        graphene.ID,
        description="Customer IDs to add to the group",
        name="customers",
    )
    variants = graphene.List(
        graphene.ID,
        description="Variants IDs to Assign to the group",
        name="variants",
    )


class CustomerGroupCreateInput(CustomerGroupInput):
    name = graphene.String(description="Name of the customer group.", required=True)


class CustomerGroupCreate(ModelMutation):
    class Arguments:
        input = CustomerGroupCreateInput(
            required=True, description="Fields required to create customer group."
        )

    class Meta:
        description = "Creates new customer group."
        model = models.CustomerGroup
        error_type_class = CustomerGroupError
        permissions = (CustomerGroupPermissions.MANAGE_GROUPS,)


class CustomerGroupUpdateInput(CustomerGroupInput):
    name = graphene.String(description="name of customer group")


class CustomerGroupUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a customer group to update")
        input = CustomerGroupUpdateInput(
            description="Fields required to update a customer group", required=True
        )

    class Meta:
        description = "Update a customer group"
        model = models.CustomerGroup
        error_type_class = CustomerGroupError
        permissions = (CustomerGroupPermissions.MANAGE_GROUPS,)


class CustomerGroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of customrt group to delete")

    class Meta:
        description = "delete the customer group"
        model = models.CustomerGroup
        error_type_class = CustomerGroupError
        permissions = (CustomerGroupPermissions.MANAGE_GROUPS,)
