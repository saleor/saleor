import graphene
from graphql_jwt.decorators import permission_required

from ..core.fields import PrefetchingConnectionField
from ..descriptions import DESCRIPTIONS
from .mutations import (
    AddressCreate, AddressDelete, AddressUpdate, CustomerCreate,
    CustomerDelete, CustomerPasswordReset, CustomerRegister, CustomerUpdate,
    PasswordReset, SetPassword, StaffCreate, StaffDelete, StaffUpdate)
from .resolvers import (
    resolve_address_validator, resolve_customers, resolve_staff_users)
from .types import AddressValidationData, AddressValidationInput, User


class AccountQueries(graphene.ObjectType):
    address_validator = graphene.Field(
        AddressValidationData,
        input=graphene.Argument(AddressValidationInput, required=True))
    user = graphene.Field(
        User, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup an user by ID.')
    customers = PrefetchingConnectionField(
        User, description='List of the shop\'s users.',
        query=graphene.String(
            description=DESCRIPTIONS['user']))
    staff_users = PrefetchingConnectionField(
        User, description='List of the shop\'s staff users.',
        query=graphene.String(description=DESCRIPTIONS['user']))

    @permission_required('account.manage_users')
    def resolve_user(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, User)

    @permission_required('account.manage_users')
    def resolve_customers(self, info, query=None, **kwargs):
        return resolve_customers(info, query=query)

    @permission_required('account.manage_staff')
    def resolve_staff_users(self, info, query=None, **kwargs):
        return resolve_staff_users(info, query=query)

    def resolve_address_validator(self, info, input):
        return resolve_address_validator(info, input)


class AccountMutations(graphene.ObjectType):
    set_password = SetPassword.Field()
    password_reset = PasswordReset.Field()

    customer_create = CustomerCreate.Field()
    customer_update = CustomerUpdate.Field()
    customer_delete = CustomerDelete.Field()
    customer_password_reset = CustomerPasswordReset.Field()
    customer_register = CustomerRegister.Field()

    staff_create = StaffCreate.Field()
    staff_update = StaffUpdate.Field()
    staff_delete = StaffDelete.Field()

    address_create = AddressCreate.Field()
    address_update = AddressUpdate.Field()
    address_delete = AddressDelete.Field()
