import graphene

from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import AccountPermissions, OrderPermissions
from ...permission.utils import message_one_of_permissions_required
from ..app.dataloaders import app_promise_callback
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
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
    """客户筛选的输入类型。"""

    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = CustomerFilter


class PermissionGroupFilterInput(FilterInputObjectType):
    """权限组筛选的输入类型。"""

    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = PermissionGroupFilter


class StaffUserInput(FilterInputObjectType):
    """员工用户筛选的输入类型。"""

    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = StaffUserFilter


class AccountQueries(graphene.ObjectType):
    """账户相关的查询。"""

    address_validation_rules = BaseField(
        AddressValidationData,
        description="返回地址验证规则。",
        country_code=graphene.Argument(
            CountryCodeEnum,
            description="两位字母的 ISO 3166-1 国家代码。",
            required=True,
        ),
        country_area=graphene.Argument(
            graphene.String, description="地区、省或州的名称。"
        ),
        city=graphene.Argument(graphene.String, description="城市或城镇的名称。"),
        city_area=graphene.Argument(
            graphene.String, description="像区一样的子区域。"
        ),
        doc_category=DOC_CATEGORY_USERS,
    )
    address = BaseField(
        Address,
        id=graphene.Argument(
            graphene.ID, description="地址的 ID。", required=True
        ),
        description="通过 ID 查找地址。"
        + message_one_of_permissions_required(
            [AccountPermissions.MANAGE_USERS, AuthorizationFilters.OWNER]
        ),
        doc_category=DOC_CATEGORY_USERS,
    )
    customers = FilterConnectionField(
        UserCountableConnection,
        filter=CustomerFilterInput(description="客户的筛选选项。"),
        sort_by=UserSortingInput(description="对客户进行排序。"),
        description="商店的客户列表。此列表包括通过 accountRegister 突变注册的所有用户。此外，使用其帐户下订单的员工用户也将显示在此列表中。",
        permissions=[OrderPermissions.MANAGE_ORDERS, AccountPermissions.MANAGE_USERS],
        doc_category=DOC_CATEGORY_USERS,
    )
    permission_groups = FilterConnectionField(
        GroupCountableConnection,
        filter=PermissionGroupFilterInput(
            description="权限组的筛选选项。"
        ),
        sort_by=PermissionGroupSortingInput(description="对权限组进行排序。"),
        description="权限组列表。",
        permissions=[AccountPermissions.MANAGE_STAFF],
        doc_category=DOC_CATEGORY_USERS,
    )
    permission_group = PermissionsField(
        Group,
        id=graphene.Argument(
            graphene.ID, description="组的 ID。", required=True
        ),
        description="通过 ID 查找权限组。",
        permissions=[AccountPermissions.MANAGE_STAFF],
        doc_category=DOC_CATEGORY_USERS,
    )
    me = BaseField(
        User,
        description="返回当前已验证的用户。",
        doc_category=DOC_CATEGORY_USERS,
    )
    staff_users = FilterConnectionField(
        UserCountableConnection,
        filter=StaffUserInput(description="员工用户的筛选选项。"),
        sort_by=UserSortingInput(description="对员工用户进行排序。"),
        description="商店的员工用户列表。",
        permissions=[AccountPermissions.MANAGE_STAFF],
        doc_category=DOC_CATEGORY_USERS,
    )
    user = PermissionsField(
        User,
        id=graphene.Argument(graphene.ID, description="用户的 ID。"),
        email=graphene.Argument(
            graphene.String, description="用户的电子邮件地址。"
        ),
        external_reference=graphene.Argument(
            graphene.String, description="用户的外部 ID。"
        ),
        permissions=[
            AccountPermissions.MANAGE_STAFF,
            AccountPermissions.MANAGE_USERS,
            OrderPermissions.MANAGE_ORDERS,
        ],
        description="通过 ID 或电子邮件地址查找用户。",
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
    """账户相关的变更。"""

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
