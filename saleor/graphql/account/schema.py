import graphene
from graphql_jwt.decorators import login_required, permission_required

from ..core.fields import FilterInputConnectionField
from ..core.types import FilterInputObjectType
from ..descriptions import DESCRIPTIONS
from .filters import CustomerFilter, StaffUserFilter
from .bulk_mutations import (
    CustomerBulkDelete, StaffBulkDelete, UserBulkSetActive)
from .mutations import (
    AddressCreate, AddressDelete, AddressSetDefault, AddressUpdate,
    CustomerAddressCreate, CustomerCreate, CustomerDelete,
    CustomerPasswordReset, CustomerRegister, CustomerSetDefaultAddress,
    CustomerUpdate, LoggedUserUpdate, PasswordReset, SetPassword, StaffCreate,
    StaffDelete, StaffUpdate, UserAvatarDelete, UserAvatarUpdate)
from .resolvers import (
    resolve_address_validator, resolve_customers, resolve_staff_users)
from .types import AddressValidationData, AddressValidationInput, User


class CustomerFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CustomerFilter


class StaffUserInput(FilterInputObjectType):
    class Meta:
        filterset_class = StaffUserFilter


class AccountQueries(graphene.ObjectType):
    address_validator = graphene.Field(
        AddressValidationData,
        input=graphene.Argument(AddressValidationInput, required=True))
    customers = FilterInputConnectionField(
        User, filter=CustomerFilterInput(),
        description='List of the shop\'s customers.',
        query=graphene.String(description=DESCRIPTIONS['user']))
    me = graphene.Field(
        User, description='Logged in user data.')
    staff_users = FilterInputConnectionField(
        User, filter=StaffUserInput(),
        description='List of the shop\'s staff users.',
        query=graphene.String(description=DESCRIPTIONS['user']))
    user = graphene.Field(
        User, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup an user by ID.')

    def resolve_address_validator(self, info, input):
        return resolve_address_validator(info, input)

    @permission_required('account.manage_users')
    def resolve_customers(self, info, query=None, **_kwargs):
        return resolve_customers(info, query=query)

    @login_required
    def resolve_me(self, info):
        return info.context.user

    @permission_required('account.manage_staff')
    def resolve_staff_users(self, info, query=None, **_kwargs):
        return resolve_staff_users(info, query=query)

    @permission_required('account.manage_users')
    def resolve_user(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, User)


class AccountMutations(graphene.ObjectType):
    password_reset = PasswordReset.Field()
    set_password = SetPassword.Field()

    customer_create = CustomerCreate.Field()
    customer_delete = CustomerDelete.Field()
    customer_bulk_delete = CustomerBulkDelete.Field()
    customer_password_reset = CustomerPasswordReset.Field()
    customer_register = CustomerRegister.Field()
    customer_update = CustomerUpdate.Field()
    customer_address_create = CustomerAddressCreate.Field()
    customer_set_default_address = CustomerSetDefaultAddress.Field()

    logged_user_update = LoggedUserUpdate.Field()

    staff_create = StaffCreate.Field()
    staff_delete = StaffDelete.Field()
    staff_bulk_delete = StaffBulkDelete.Field()
    staff_update = StaffUpdate.Field()

    address_create = AddressCreate.Field()
    address_delete = AddressDelete.Field()
    address_update = AddressUpdate.Field()
    address_set_default = AddressSetDefault.Field()

    user_avatar_update = UserAvatarUpdate.Field()
    user_avatar_delete = UserAvatarDelete.Field()
    user_bulk_set_active = UserBulkSetActive.Field()
