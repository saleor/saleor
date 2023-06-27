import graphene

from saleor.graphql.core import ResolveInfo
from .types import CustomerGroup
from ....core.tracing import traced_atomic_transaction
from ...core import ResolveInfo
from ...core.mutations import ModelMutation, BaseMutation, ModelDeleteMutation
from ...account.enums import CountryCodeEnum
from ...account.types import User
from ....b2b import models
from ....permission.enums import AccountPermissions
from ....permission.auth_filters import AuthorizationFilters
from ...core.types import AccountError, NonNullList
from ..customer_group.types import CustomerGroup


class CustomerGroupInput(graphene.InputObjectType):
    name = graphene.String()
    channel = graphene.ID()


class CreateCustomerGroup(ModelMutation):
    class Arguments:
        input = CustomerGroupInput(required=True)

    class Meta:
        description = "Create a customer group"
        model = models.CustomerGroup
        object_type = CustomerGroup
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

class UpdateCustomerGroup(ModelMutation):
    class Arguments:
        id = graphene.Argument(graphene.ID)
        input = CustomerGroupInput(required=True)

    class Meta:
        description = "Update customer group"
        model = models.CustomerGroup
        object_type = CustomerGroup
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

class AppointCustomersToGroup(BaseMutation):
    customer_group = graphene.Field(
        CustomerGroup, description="Customer group to which the customers will be added to"
    )

    class Arguments:
        customer_group_id = graphene.Argument(
            graphene.ID, required=True, description="ID of the group"
        )
        customers = NonNullList(
            graphene.String, required=True, description="List of customer emails by which they will be added to group"
        )

    class Meta:
        description = "Adds customers to a customer group."
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /, *, customer_group_id, customers):
        customer_group = cls.get_node_or_error(_info, customer_group_id, field="customer_group_id", only_type=CustomerGroup)
        with traced_atomic_transaction():
            for i in customers:
                user = models.User.objects.filter(email=i).first()
                if user:
                    company_info = models.CompanyInfo.objects.filter(customer=user).first()
                    if company_info != None and company_info.has_access_to_b2b == True:
                        user.customer_group=customer_group
                        user.save()
                    else:
                        pass
                else:
                    pass
        return AppointCustomersToGroup(customer_group=customer_group)


class RemoveCustomersFromGroup(BaseMutation):
    customer_group = graphene.Field(
        CustomerGroup, description="Customer group to which the customers will be added to"
    )

    class Arguments:
        customer_group_id = graphene.Argument(
            graphene.ID, required=True, description="ID of the group"
        )
        customers = NonNullList(
            graphene.String, required=True, description="List of customer emails by which they will be added to group"
        )

    class Meta:
        description = "Removes customers from group"
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /, *, customer_group_id, customers):
        customer_group = cls.get_node_or_error(_info, customer_group_id, field="customer_group_id", only_type=CustomerGroup)
        with traced_atomic_transaction():
            for i in customers:
                user = models.User.objects.filter(email=i, customer_group=customer_group).first()
                if user:
                    user.customer_group = None
                    user.save
        return RemoveCustomersFromGroup(customer_group=customer_group)
    

class DeleteCustomerGroup(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=False)

    class Meta:
        description = "Deletes a customer group."
        model = models.CustomerGroup
        object_type = CustomerGroup
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"