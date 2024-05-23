import graphene

from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import AccountPermissions, OrderPermissions
from ...permission.utils import message_one_of_permissions_required
from ..app.dataloaders import app_promise_callback
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_310
from ..core.doc_category import DOC_CATEGORY_USERS
from ..core.fields import BaseField, FilterConnectionField, PermissionsField
from ..core.types import FilterInputObjectType
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
from .bulk_mutations import (
    CustomerBulkDelete,
    CustomerBulkUpdate,
    StaffBulkDelete,
    UserBulkSetActive,
)
from .enums import CountryCodeEnum
from .filters import CustomerFilter, PermissionGroupFilter, StaffUserFilter
from .mutations.account import (
    AccountAddressCreate,
    AccountAddressDelete,
    AccountAddressUpdate,
    AccountDelete,
    AccountRegister,
    AccountRequestDeletion,
    AccountSetDefaultAddress,
    AccountUpdate,
    ConfirmAccount,
    ConfirmEmailChange,
    RequestEmailChange,
    SendConfirmationEmail,
)
from .mutations.authentication import (
    CreateToken,
    DeactivateAllUserTokens,
    ExternalAuthenticationUrl,
    ExternalLogout,
    ExternalObtainAccessTokens,
    ExternalRefresh,
    ExternalVerify,
    PasswordChange,
    RefreshToken,
    RequestPasswordReset,
    SetPassword,
    VerifyToken,
)
from .mutations.permission_group import (
    PermissionGroupCreate,
    PermissionGroupDelete,
    PermissionGroupUpdate,
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
)
from .resolvers import (
    resolve_address,
    resolve_address_validation_rules,
    resolve_customers,
    resolve_permission_group,
    resolve_permission_groups,
    resolve_staff_users,
    resolve_user,
)
from .sorters import PermissionGroupSortingInput, UserSortingInput
from .types import (
    Address,
    AddressValidationData,
    Group,
    GroupCountableConnection,
    User,
    UserCountableConnection,
)


class CustomerFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = CustomerFilter


class PermissionGroupFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = PermissionGroupFilter


class StaffUserInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = StaffUserFilter


class AccountQueries(graphene.ObjectType):
    address_validation_rules = BaseField(
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
        doc_category=DOC_CATEGORY_USERS,
    )
    address = BaseField(
        Address,
        id=graphene.Argument(
            graphene.ID, description="ID of an address.", required=True
        ),
        description="Look up an address by ID."
        + message_one_of_permissions_required(
            [AccountPermissions.MANAGE_USERS, AuthorizationFilters.OWNER]
        ),
        doc_category=DOC_CATEGORY_USERS,
    )
    customers = FilterConnectionField(
        UserCountableConnection,
        filter=CustomerFilterInput(description="Filtering options for customers."),
        sort_by=UserSortingInput(description="Sort customers."),
        description="List of the shop's customers. This list includes all users who registered through the accountRegister mutation. Additionally, staff users who have placed an order using their account will also appear in this list.",
        permissions=[OrderPermissions.MANAGE_ORDERS, AccountPermissions.MANAGE_USERS],
        doc_category=DOC_CATEGORY_USERS,
    )
    permission_groups = FilterConnectionField(
        GroupCountableConnection,
        filter=PermissionGroupFilterInput(
            description="Filtering options for permission groups."
        ),
        sort_by=PermissionGroupSortingInput(description="Sort permission groups."),
        description="List of permission groups.",
        permissions=[AccountPermissions.MANAGE_STAFF],
        doc_category=DOC_CATEGORY_USERS,
    )
    permission_group = PermissionsField(
        Group,
        id=graphene.Argument(
            graphene.ID, description="ID of the group.", required=True
        ),
        description="Look up permission group by ID.",
        permissions=[AccountPermissions.MANAGE_STAFF],
        doc_category=DOC_CATEGORY_USERS,
    )
    me = BaseField(
        User,
        description="Return the currently authenticated user.",
        doc_category=DOC_CATEGORY_USERS,
    )
    staff_users = FilterConnectionField(
        UserCountableConnection,
        filter=StaffUserInput(description="Filtering options for staff users."),
        sort_by=UserSortingInput(description="Sort staff users."),
        description="List of the shop's staff users.",
        permissions=[AccountPermissions.MANAGE_STAFF],
        doc_category=DOC_CATEGORY_USERS,
    )
    user = PermissionsField(
        User,
        id=graphene.Argument(graphene.ID, description="ID of the user."),
        email=graphene.Argument(
            graphene.String, description="Email address of the user."
        ),
        external_reference=graphene.Argument(
            graphene.String, description=f"External ID of the user. {ADDED_IN_310}"
        ),
        permissions=[
            AccountPermissions.MANAGE_STAFF,
            AccountPermissions.MANAGE_USERS,
            OrderPermissions.MANAGE_ORDERS,
        ],
        description="Look up a user by ID or email address.",
        doc_category=DOC_CATEGORY_USERS,
    )

    @staticmethod
    def resolve_address_validation_rules(
        _root,
        info: ResolveInfo,
        *,
        country_code,
        country_area=None,
        city=None,
        city_area=None,
    ):
        return resolve_address_validation_rules(
            info,
            country_code,
            country_area=country_area,
            city=city,
            city_area=city_area,
        )

    @staticmethod
    def resolve_customers(_root, info: ResolveInfo, **kwargs):
        qs = resolve_customers(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, UserCountableConnection)

    @staticmethod
    def resolve_permission_groups(_root, info: ResolveInfo, **kwargs):
        qs = resolve_permission_groups(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, GroupCountableConnection)

    @staticmethod
    def resolve_permission_group(_root, info: ResolveInfo, *, id):
        _, id = from_global_id_or_error(id, Group)
        return resolve_permission_group(info, id)

    @staticmethod
    def resolve_me(_root, info):
        user = info.context.user
        return user if user else None

    @staticmethod
    def resolve_staff_users(_root, info: ResolveInfo, **kwargs):
        qs = resolve_staff_users(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, UserCountableConnection)

    @staticmethod
    def resolve_user(
        _root, info: ResolveInfo, *, id=None, email=None, external_reference=None
    ):
        validate_one_of_args_is_in_query(
            "id", id, "email", email, "external_reference", external_reference
        )
        return resolve_user(info, id, email, external_reference)

    @staticmethod
    @app_promise_callback
    def resolve_address(_root, info: ResolveInfo, app, *, id):
        return resolve_address(info, id, app)


class AccountMutations(graphene.ObjectType):
    # Base mutations
    token_create = CreateToken.Field()
    token_refresh = RefreshToken.Field()
    token_verify = VerifyToken.Field()
    tokens_deactivate_all = DeactivateAllUserTokens.Field()

    external_authentication_url = ExternalAuthenticationUrl.Field()
    external_obtain_access_tokens = ExternalObtainAccessTokens.Field()

    external_refresh = ExternalRefresh.Field()
    external_logout = ExternalLogout.Field()
    external_verify = ExternalVerify.Field()

    request_password_reset = RequestPasswordReset.Field()
    send_confirmation_email = SendConfirmationEmail.Field()
    confirm_account = ConfirmAccount.Field()
    set_password = SetPassword.Field()
    password_change = PasswordChange.Field()
    request_email_change = RequestEmailChange.Field()
    confirm_email_change = ConfirmEmailChange.Field()

    # Account mutations
    account_address_create = AccountAddressCreate.Field()
    account_address_update = AccountAddressUpdate.Field()
    account_address_delete = AccountAddressDelete.Field()
    account_set_default_address = AccountSetDefaultAddress.Field()

    account_register = AccountRegister.Field()
    account_update = AccountUpdate.Field()
    account_request_deletion = AccountRequestDeletion.Field()
    account_delete = AccountDelete.Field()

    # Staff mutations
    address_create = AddressCreate.Field()
    address_update = AddressUpdate.Field()
    address_delete = AddressDelete.Field()
    address_set_default = AddressSetDefault.Field()

    customer_create = CustomerCreate.Field()
    customer_update = CustomerUpdate.Field()
    customer_delete = CustomerDelete.Field()
    customer_bulk_delete = CustomerBulkDelete.Field()
    customer_bulk_update = CustomerBulkUpdate.Field()

    staff_create = StaffCreate.Field()
    staff_update = StaffUpdate.Field()
    staff_delete = StaffDelete.Field()
    staff_bulk_delete = StaffBulkDelete.Field()

    user_avatar_update = UserAvatarUpdate.Field()
    user_avatar_delete = UserAvatarDelete.Field()
    user_bulk_set_active = UserBulkSetActive.Field()

    # Permission group mutations
    permission_group_create = PermissionGroupCreate.Field()
    permission_group_update = PermissionGroupUpdate.Field()
    permission_group_delete = PermissionGroupDelete.Field()
