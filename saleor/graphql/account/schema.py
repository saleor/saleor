import graphene
from graphql_jwt.decorators import login_required, permission_required

from ..core.fields import FilterInputConnectionField
from ..core.types import FilterInputObjectType
from ..descriptions import DESCRIPTIONS
from .bulk_mutations import CustomerBulkDelete, StaffBulkDelete, UserBulkSetActive
from .enums import CountryCodeEnum
from .filters import CustomerFilter, StaffUserFilter
from .mutations.account import (
    AccountAddressCreate,
    AccountAddressDelete,
    AccountAddressUpdate,
    AccountDelete,
    AccountRegister,
    AccountRequestDeletion,
    AccountSetDefaultAddress,
    AccountUpdate,
)
from .mutations.base import (
    PasswordChange,
    RequestPasswordReset,
    SetPassword,
    UserClearStoredMeta,
    UserUpdateMeta,
)
from .mutations.deprecated_account import (
    CustomerAddressCreate,
    CustomerPasswordReset,
    CustomerRegister,
    CustomerSetDefaultAddress,
    LoggedUserUpdate,
)
from .mutations.deprecated_staff import PasswordReset
from .mutations.staff import (
    AddressCreate,
    AddressDelete,
    AddressSetDefault,
    AddressUpdate,
    CustomerCreate,
    CustomerDelete,
    CustomerUpdate,
    StaffCreate,
    StaffDelete,
    StaffUpdate,
    UserAvatarDelete,
    UserAvatarUpdate,
    UserClearStoredPrivateMeta,
    UserUpdatePrivateMeta,
)
from .resolvers import resolve_address_validator, resolve_customers, resolve_staff_users
from .types import AddressValidationData, User


class CustomerFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CustomerFilter


class StaffUserInput(FilterInputObjectType):
    class Meta:
        filterset_class = StaffUserFilter


class AccountQueries(graphene.ObjectType):
    address_validation_rules = graphene.Field(
        AddressValidationData,
        country_code=graphene.Argument(CountryCodeEnum, required=False),
        country_area=graphene.String(required=False),
        city_area=graphene.String(required=False),
    )
    customers = FilterInputConnectionField(
        User,
        filter=CustomerFilterInput(),
        description="List of the shop's customers.",
        query=graphene.String(description=DESCRIPTIONS["user"]),
    )
    me = graphene.Field(User, description="Logged in user data.")
    staff_users = FilterInputConnectionField(
        User,
        filter=StaffUserInput(),
        description="List of the shop's staff users.",
        query=graphene.String(description=DESCRIPTIONS["user"]),
    )
    user = graphene.Field(
        User,
        id=graphene.Argument(graphene.ID, required=True),
        description="Lookup an user by ID.",
    )

    def resolve_address_validation_rules(
        self, info, country_code=None, country_area=None, city_area=None
    ):
        return resolve_address_validator(
            info,
            country_code=country_code,
            country_area=country_area,
            city_area=city_area,
        )

    @permission_required("account.manage_users")
    def resolve_customers(self, info, query=None, **_kwargs):
        return resolve_customers(info, query=query)

    @login_required
    def resolve_me(self, info):
        return info.context.user

    @permission_required("account.manage_staff")
    def resolve_staff_users(self, info, query=None, **_kwargs):
        return resolve_staff_users(info, query=query)

    @permission_required("account.manage_users")
    def resolve_user(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, User)


class AccountMutations(graphene.ObjectType):
    # Base mutations
    request_password_reset = RequestPasswordReset.Field()
    set_password = SetPassword.Field()
    password_change = PasswordChange.Field()

    user_update_metadata = UserUpdateMeta.Field()
    user_clear_stored_metadata = UserClearStoredMeta.Field()

    # Account mutations
    account_address_create = AccountAddressCreate.Field()
    account_address_update = AccountAddressUpdate.Field()
    account_address_delete = AccountAddressDelete.Field()
    account_set_default_address = AccountSetDefaultAddress.Field()

    account_register = AccountRegister.Field()
    account_update = AccountUpdate.Field()
    account_request_deletion = AccountRequestDeletion.Field()
    account_delete = AccountDelete.Field()

    # Account deprecated mutations
    customer_password_reset = CustomerPasswordReset.Field()

    customer_address_create = CustomerAddressCreate.Field()
    customer_set_default_address = CustomerSetDefaultAddress.Field()

    customer_register = CustomerRegister.Field()
    logged_user_update = LoggedUserUpdate.Field()

    # Staff mutation
    address_create = AddressCreate.Field()
    address_update = AddressUpdate.Field()
    address_delete = AddressDelete.Field()
    address_set_default = AddressSetDefault.Field()

    customer_create = CustomerCreate.Field()
    customer_update = CustomerUpdate.Field()
    customer_delete = CustomerDelete.Field()
    customer_bulk_delete = CustomerBulkDelete.Field()

    staff_create = StaffCreate.Field()
    staff_update = StaffUpdate.Field()
    staff_delete = StaffDelete.Field()
    staff_bulk_delete = StaffBulkDelete.Field()

    user_avatar_update = UserAvatarUpdate.Field()
    user_avatar_delete = UserAvatarDelete.Field()
    user_bulk_set_active = UserBulkSetActive.Field()

    user_update_private_metadata = UserUpdatePrivateMeta.Field()
    user_clear_stored_private_metadata = UserClearStoredPrivateMeta.Field()

    # Staff deprecated mutation
    password_reset = PasswordReset.Field()
