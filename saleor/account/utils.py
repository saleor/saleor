from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import Exists, OuterRef

from ..app.models import App
from ..checkout import AddressType
from ..core.utils.events import call_event
from ..permission.models import Permission
from ..plugins.manager import get_plugins_manager
from .models import Group, User

if TYPE_CHECKING:
    from ..plugins.manager import PluginsManager
    from .models import Address


@dataclass
class RequestorAwareContext:
    """一个数据类，用于存储请求者的上下文信息。

    这个类用于在不同的层之间传递请求者的信息，例如用户或应用，
    以及是否允许使用数据库副本。

    Attributes:
        allow_replica (bool): 是否允许使用数据库副本。
        user (User | None): 发出请求的用户。
        app (App | None): 发出请求的应用。
    """

    allow_replica: bool
    user: User | None = None
    app: App | None = None

    @property
    def META(self):
        """返回一个空的 META 字典，以模仿 Django 的请求对象。"""
        return {}

    @staticmethod
    def _get_or_none(model, pk_value):
        """根据主键从数据库副本中获取一个对象，如果不存在则返回 None。"""
        return (
            model.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .filter(pk=pk_value)
            .first()
            if pk_value
            else None
        )

    @classmethod
    def from_context_data(cls, context_data):
        """从上下文数据字典创建一个 RequestorAwareContext 实例。"""
        return cls(
            allow_replica=context_data["allow_replica"],
            user=cls._get_or_none(User, context_data["user_pk"]),
            app=cls._get_or_none(App, context_data["app_pk"]),
        )

    @staticmethod
    def create_context_data(context):
        """从一个上下文实例（如 GraphQL 的上下文）创建一个上下文数据字典。"""
        return {
            "allow_replica": context.allow_replica,
            "user_pk": context.user.pk if context.user else None,
            "app_pk": context.app.pk if context.app else None,
        }


def store_user_address(
    user: User,
    address: "Address",
    address_type: str,
    manager: "PluginsManager",
):
    """将地址添加到用户地址簿并设置为默认地址。

    如果用户已达到最大地址数限制，则不存储新地址。
    如果地址已存在于用户的地址簿中，则不创建新地址。
    如果用户没有该类型的默认地址，则将此地址设置为默认地址。

    Args:
        user (User): 要添加地址的用户。
        address (Address): 要添加的地址。
        address_type (str): 地址类型（计费或送货）。
        manager (PluginsManager): 插件管理器实例。
    """
    # user can only have specified number of addresses
    # so we do not want to store additional one if user already reached the max
    # number of addresses
    if is_user_address_limit_reached(user):
        return

    address_data = address.as_data()

    address = user.addresses.filter(**address_data).first()
    if address is None:
        address = user.addresses.create(**address_data)

    if address_type == AddressType.BILLING:
        if not user.default_billing_address:
            set_user_default_billing_address(user, address)
    elif address_type == AddressType.SHIPPING:
        if not user.default_shipping_address:
            set_user_default_shipping_address(user, address)


def is_user_address_limit_reached(user: "User"):
    """如果用户不能拥有更多地址，则返回 True。"""
    return user.addresses.count() >= settings.MAX_USER_ADDRESSES


def remove_the_oldest_user_address_if_address_limit_is_reached(user: "User"):
    """当达到最大地址限制时，删除最旧的用户地址。"""
    if is_user_address_limit_reached(user):
        remove_the_oldest_user_address(user)


def remove_the_oldest_user_address(user: "User"):
    """删除最旧的用户地址。

    不包括默认的计费和送货地址。
    """
    user_default_addresses_ids = [
        user.default_billing_address_id,
        user.default_shipping_address_id,
    ]
    user_address = (
        user.addresses.exclude(pk__in=user_default_addresses_ids).order_by("pk").first()
    )
    if user_address:
        user_address.delete()


def set_user_default_billing_address(user, address):
    """将用户的默认计费地址设置为给定地址。"""
    user.default_billing_address = address
    user.save(update_fields=["default_billing_address", "updated_at"])


def set_user_default_shipping_address(user, address):
    """将用户的默认送货地址设置为给定地址。"""
    user.default_shipping_address = address
    user.save(update_fields=["default_shipping_address", "updated_at"])


def change_user_default_address(
    user: User, address: "Address", address_type: str, manager: "PluginsManager"
):
    """更改用户的默认地址。

    如果用户已有该类型的默认地址，则将其添加回地址簿。
    然后将新地址设置为默认地址。

    Args:
        user (User): 要更改默认地址的用户。
        address (Address): 新的默认地址。
        address_type (str): 地址类型（计费或送货）。
        manager (PluginsManager): 插件管理器实例。
    """
    if address_type == AddressType.BILLING:
        if user.default_billing_address:
            user.addresses.add(user.default_billing_address)
        set_user_default_billing_address(user, address)
    elif address_type == AddressType.SHIPPING:
        if user.default_shipping_address:
            user.addresses.add(user.default_shipping_address)
        set_user_default_shipping_address(user, address)


def create_superuser(credentials):
    """使用给定的凭据创建一个超级用户。

    如果用户已存在，则不执行任何操作。

    Args:
        credentials (dict): 包含“email”和“password”的字典。

    Returns:
        str: 一条描述操作结果的消息。
    """
    user, created = User.objects.get_or_create(
        email=credentials["email"],
        defaults={"is_active": True, "is_staff": True, "is_superuser": True},
    )
    if created:
        user.set_password(credentials["password"])
        user.save()
        msg = f"Superuser - {credentials['email']}/{credentials['password']}"
    else:
        msg = f"Superuser already exists - {credentials['email']}"
    return msg


def remove_staff_member(staff):
    """仅当员工没有下过订单时才删除其帐户。

    否则，将其 is_staff 状态切换为 False。
    """
    if staff.orders.exists():
        staff.is_staff = False
        staff.user_permissions.clear()
        staff.save()
    else:
        staff.delete()


def retrieve_user_by_email(email):
    """通过电子邮件检索用户。

    电子邮件查找不区分大小写，除非查询返回多个用户。
    在这种情况下，函数返回区分大小写的结果。

    Args:
        email (str): 要检索的用户的电子邮件地址。

    Returns:
        User | None: 找到的用户，或 None。
    """
    users = list(User.objects.filter(email__iexact=email))

    if len(users) > 1:
        users_exact = [user for user in users if user.email == email]
        users_iexact = [user for user in users if user.email == email.lower()]
        users = users_exact or users_iexact

    if users:
        return users[0]
    return None


def get_user_groups_permissions(user: User):
    """获取用户通过其组拥有的所有权限。

    Args:
        user (User): 要获取权限的用户。

    Returns:
        QuerySet[Permission]: 用户通过组拥有的权限查询集。
    """
    GroupUser = User.groups.through
    group_users = GroupUser._default_manager.filter(user_id=user.id).values("group_id")
    GroupPermissions = Group.permissions.through
    group_permissions = GroupPermissions.objects.filter(
        Exists(group_users.filter(group_id=OuterRef("group_id")))
    ).values("permission_id")
    return Permission.objects.filter(
        Exists(group_permissions.filter(permission_id=OuterRef("id")))
    )


def send_user_event(user: User, created: bool, updated: bool):
    """为用户发送创建或更新事件。

    根据用户的 is_staff 状态，触发 staff_* 或 customer_* 事件。

    Args:
        user (User): 相关的用户。
        created (bool): 如果用户是新创建的，则为 True。
        updated (bool): 如果用户已更新，则为 True。
    """
    manager = get_plugins_manager(allow_replica=False)
    event = None
    if created:
        event = manager.staff_created if user.is_staff else manager.customer_created
    elif updated:
        event = manager.staff_updated if user.is_staff else manager.customer_updated
    if event:
        call_event(event, user)
