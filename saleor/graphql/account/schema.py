import graphene
from graphql_jwt.decorators import login_required

from ..core.fields import FilterInputConnectionField
from ..core.types import FilterInputObjectType
from ..decorators import one_of_permissions_required, permission_required
from ..descriptions import DESCRIPTIONS
from .bulk_mutations import CustomerBulkDelete, StaffBulkDelete, UserBulkSetActive
from .enums import CountryCodeEnum
from .filters import CustomerFilter, ServiceAccountFilter, StaffUserFilter
from .mutations.account import (
    AccountAddressCreate,
    AccountAddressDelete,
    AccountAddressUpdate,
    AccountDelete,
    AccountRegister,
    AccountRequestDeletion,
    AccountSetDefaultAddress,
    AccountUpdate,
    AccountUpdateMeta,
)
from .mutations.base import (
    PasswordChange,
    RequestPasswordReset,
    SetPassword,
    UserClearMeta,
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
from .mutations.service_account import (
    ServiceAccountClearPrivateMeta,
    ServiceAccountCreate,
    ServiceAccountDelete,
    ServiceAccountTokenCreate,
    ServiceAccountTokenDelete,
    ServiceAccountUpdate,
    ServiceAccountUpdatePrivateMeta,
)
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
    UserClearPrivateMeta,
    UserUpdatePrivateMeta,
)
from .resolvers import (
    resolve_address_validation_rules,
    resolve_customers,
    resolve_service_accounts,
    resolve_staff_users,
    resolve_user,
)
from .types import AddressValidationData, ServiceAccount, User


class CustomerFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CustomerFilter


class StaffUserInput(FilterInputObjectType):
    class Meta:
        filterset_class = StaffUserFilter


class ServiceAccountFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ServiceAccountFilter


class AccountQueries(graphene.ObjectType):
    address_validation_rules = graphene.Field(
        AddressValidationData,
        description="Returns address validation rules.",
        country_code=graphene.Argument(
            CountryCodeEnum,
            description="Two-letter ISO 3166-1 country code.",
            required=True,
        ),
        country_area=graphene.Argument(
            graphene.String, description="Designation of a region, province or state."
        ),
        city=graphene.Argument(graphene.String, description="City or a town name."),
        city_area=graphene.Argument(
            graphene.String, description="Sublocality like a district."
        ),
    )
    customers = FilterInputConnectionField(
        User,
        filter=CustomerFilterInput(description="Filtering options for customers."),
        description="List of the shop's customers.",
        query=graphene.String(description=DESCRIPTIONS["user"]),
    )
    me = graphene.Field(User, description="Return the currently authenticated user.")
    staff_users = FilterInputConnectionField(
        User,
        filter=StaffUserInput(description="Filtering options for staff users."),
        description="List of the shop's staff users.",
        query=graphene.String(description=DESCRIPTIONS["user"]),
    )
    service_accounts = FilterInputConnectionField(
        ServiceAccount,
        filter=ServiceAccountFilterInput(
            description="Filtering options for service accounts."
        ),
        description="List of the service accounts.",
    )
    service_account = graphene.Field(
        ServiceAccount,
        id=graphene.Argument(
            graphene.ID, description="ID of the service account.", required=True
        ),
        description="Look up a service account by ID.",
    )

    user = graphene.Field(
        User,
        id=graphene.Argument(graphene.ID, description="ID of the user.", required=True),
        description="Look up a user by ID.",
    )

    def resolve_address_validation_rules(
        self, info, country_code, country_area=None, city=None, city_area=None
    ):
        return resolve_address_validation_rules(
            info,
            country_code,
            country_area=country_area,
            city=city,
            city_area=city_area,
        )

    @permission_required("account.manage_service_accounts")
    def resolve_service_accounts(self, info, **_kwargs):
        return resolve_service_accounts(info)

    @permission_required("account.manage_service_accounts")
    def resolve_service_account(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ServiceAccount)

    @permission_required("account.manage_users")
    def resolve_customers(self, info, query=None, **_kwargs):
        return resolve_customers(info, query=query)

    @login_required
    def resolve_me(self, info):
        return info.context.user

    @permission_required("account.manage_staff")
    def resolve_staff_users(self, info, query=None, **_kwargs):
        return resolve_staff_users(info, query=query)

    @one_of_permissions_required(["account.manage_staff", "account.manage_users"])
    def resolve_user(self, info, id):
        return resolve_user(info, id)


class AccountMutations(graphene.ObjectType):
    # Base mutations
    request_password_reset = RequestPasswordReset.Field()
    set_password = SetPassword.Field()
    password_change = PasswordChange.Field()

    # Account mutations
    account_address_create = AccountAddressCreate.Field()
    account_address_update = AccountAddressUpdate.Field()
    account_address_delete = AccountAddressDelete.Field()
    account_set_default_address = AccountSetDefaultAddress.Field()

    account_register = AccountRegister.Field()
    account_update = AccountUpdate.Field()
    account_request_deletion = AccountRequestDeletion.Field()
    account_delete = AccountDelete.Field()

    account_update_meta = AccountUpdateMeta.Field()

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

    user_update_metadata = UserUpdateMeta.Field()
    user_clear_metadata = UserClearMeta.Field()

    user_update_private_metadata = UserUpdatePrivateMeta.Field()
    user_clear_private_metadata = UserClearPrivateMeta.Field()

    service_account_create = ServiceAccountCreate.Field()
    service_account_update = ServiceAccountUpdate.Field()
    service_account_delete = ServiceAccountDelete.Field()

    service_account_update_private_metadata = ServiceAccountUpdatePrivateMeta.Field()
    service_account_clear_private_metadata = ServiceAccountClearPrivateMeta.Field()

    service_account_token_create = ServiceAccountTokenCreate.Field()
    service_account_token_delete = ServiceAccountTokenDelete.Field()

    # Staff deprecated mutation
    password_reset = PasswordReset.Field()
