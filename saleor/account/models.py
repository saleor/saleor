from collections.abc import Iterable
from functools import partial
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import JSONField, Q, Value
from django.db.models.expressions import Exists, OuterRef
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.crypto import get_random_string
from django_countries.fields import Country, CountryField
from phonenumber_field.modelfields import PhoneNumber, PhoneNumberField

from ..app.models import App
from ..core.models import ModelWithExternalReference, ModelWithMetadata
from ..core.utils.json_serializer import CustomJsonEncoder
from ..order.models import Order
from ..permission.enums import AccountPermissions, BasePermissionEnum, get_permissions
from ..permission.models import Permission, PermissionsMixin, _user_has_perm
from ..site.models import SiteSettings
from . import CustomerEvents
from .validators import validate_possible_number


class PossiblePhoneNumberField(PhoneNumberField):
    """一个对写入数据库的电话号码要求不那么严格的字段。

    覆盖了默认的验证器，使用一个更宽松的电话号码验证。
    """

    default_validators = [validate_possible_number]


class AddressQueryset(models.QuerySet["Address"]):
    """地址模型的自定义查询集。"""

    def annotate_default(self, user):
        """为地址查询集添加用户默认地址的注解。

        Args:
            user (User): 需要注解地址的用户实例。

        Returns:
            QuerySet: 带有 `user_default_shipping_address_pk` 和
                      `user_default_billing_address_pk` 注解的地址查询集。
        """
        # Set default shipping/billing address pk to None
        # if default shipping/billing address doesn't exist
        default_shipping_address_pk, default_billing_address_pk = None, None
        if user.default_shipping_address:
            default_shipping_address_pk = user.default_shipping_address.pk
        if user.default_billing_address:
            default_billing_address_pk = user.default_billing_address.pk

        return user.addresses.annotate(
            user_default_shipping_address_pk=Value(
                default_shipping_address_pk, models.IntegerField()
            ),
            user_default_billing_address_pk=Value(
                default_billing_address_pk, models.IntegerField()
            ),
        )


AddressManager = models.Manager.from_queryset(AddressQueryset)


class Address(ModelWithMetadata):
    """地址模型，代表客户或仓库的地址。

    Attributes:
        first_name (str): 名字。
        last_name (str): 姓氏。
        company_name (str): 公司名称。
        street_address_1 (str): 街道地址第一行。
        street_address_2 (str): 街道地址第二行。
        city (str): 城市。
        city_area (str): 城市区域/区。
        postal_code (str): 邮政编码。
        country (CountryField): 国家。
        country_area (str): 国家区域/省/州。
        phone (PossiblePhoneNumberField): 电话号码。
        validation_skipped (bool): 是否跳过验证。
    """

    first_name = models.CharField(max_length=256, blank=True)
    last_name = models.CharField(max_length=256, blank=True)
    company_name = models.CharField(max_length=256, blank=True)
    street_address_1 = models.CharField(max_length=256, blank=True)
    street_address_2 = models.CharField(max_length=256, blank=True)
    city = models.CharField(max_length=256, blank=True)
    city_area = models.CharField(max_length=128, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = CountryField()
    country_area = models.CharField(max_length=128, blank=True)
    phone = PossiblePhoneNumberField(blank=True, default="", db_index=True)
    validation_skipped = models.BooleanField(default=False)

    objects = AddressManager()

    class Meta:
        ordering = ("pk",)
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            GinIndex(
                name="address_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["first_name", "last_name", "city", "country"],
                opclasses=["gin_trgm_ops"] * 4,
            ),
            GinIndex(
                name="warehouse_address_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=[
                    "company_name",
                    "street_address_1",
                    "street_address_2",
                    "city",
                    "postal_code",
                    "phone",
                ],
                opclasses=["gin_trgm_ops"] * 6,
            ),
        ]

    def __eq__(self, other):
        if not isinstance(other, Address):
            return False
        return self.as_data() == other.as_data()

    __hash__ = models.Model.__hash__

    def as_data(self):
        """将地址信息作为字典返回，适合作为 kwargs 传递。

        返回结果不包含主键或关联的用户。

        Returns:
            dict: 包含地址信息的字典。
        """
        data = model_to_dict(self, exclude=["id", "user"])
        if isinstance(data["country"], Country):
            data["country"] = data["country"].code
        if isinstance(data["phone"], PhoneNumber) and not data["validation_skipped"]:
            data["phone"] = data["phone"].as_e164
        return data

    def get_copy(self):
        """返回一个具有相同地址信息的新实例。

        Returns:
            Address:一个新的地址实例。
        """
        return Address.objects.create(**self.as_data())


class UserManager(BaseUserManager["User"]):
    """用户模型的自定义管理器。"""

    def create_user(
        self, email, password=None, is_staff=False, is_active=True, **extra_fields
    ):
        """使用给定的电子邮件和密码创建一个用户实例。

        Args:
            email (str): 用户的电子邮件地址。
            password (str, optional): 用户的密码。默认为 None。
            is_staff (bool, optional): 用户是否为员工。默认为 False。
            is_active (bool, optional): 用户是否为活动状态。默认为 True。
            **extra_fields: 其他额外的字段。

        Returns:
            User: 创建的用户实例。
        """
        email = UserManager.normalize_email(email)
        # Google OAuth2 backend send unnecessary username field
        extra_fields.pop("username", None)

        user = self.model(
            email=email, is_active=is_active, is_staff=is_staff, **extra_fields
        )
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """创建一个超级用户。

        Args:
            email (str): 用户的电子邮件地址。
            password (str, optional): 用户的密码。默认为 None。
            **extra_fields: 其他额外的字段。

        Returns:
            User: 创建的超级用户实例。
        """
        user = self.create_user(
            email, password, is_staff=True, is_superuser=True, **extra_fields
        )
        group, created = Group.objects.get_or_create(name="Full Access")
        if created:
            group.permissions.add(*get_permissions())
        group.user_set.add(user)  # type: ignore[attr-defined]
        return user

    def customers(self):
        """返回客户用户的查询集。

        客户是那些非员工用户，或者是下过订单的员工。

        Returns:
            QuerySet: 客户用户的查询集。
        """
        orders = Order.objects.values("user_id")
        return self.get_queryset().filter(
            Q(is_staff=False)
            | (Q(is_staff=True) & (Exists(orders.filter(user_id=OuterRef("pk")))))
        )

    def staff(self):
        """返回员工用户的查询集。

        Returns:
            QuerySet: 员工用户的查询集。
        """
        return self.get_queryset().filter(is_staff=True)


class User(
    PermissionsMixin, ModelWithMetadata, AbstractBaseUser, ModelWithExternalReference
):
    """用户模型，代表客户和员工。

    这是一个自定义的用户模型，继承自 Django 的 `AbstractBaseUser` 和 `PermissionsMixin`。
    它使用电子邮件作为用户名字段。
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=256, blank=True)
    last_name = models.CharField(max_length=256, blank=True)
    addresses = models.ManyToManyField(
        Address, blank=True, related_name="user_addresses"
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_confirmed = models.BooleanField(default=True)
    last_confirm_email_request = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    last_password_reset_request = models.DateTimeField(null=True, blank=True)
    default_shipping_address = models.ForeignKey(
        Address, related_name="+", null=True, blank=True, on_delete=models.SET_NULL
    )
    default_billing_address = models.ForeignKey(
        Address, related_name="+", null=True, blank=True, on_delete=models.SET_NULL
    )
    avatar = models.ImageField(upload_to="user-avatars", blank=True, null=True)
    jwt_token_key = models.CharField(
        max_length=12, default=partial(get_random_string, length=12)
    )
    language_code = models.CharField(
        max_length=35, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE
    )
    search_document = models.TextField(blank=True, default="")
    uuid = models.UUIDField(default=uuid4, unique=True)

    USERNAME_FIELD = "email"
    NEWLY_CREATED_USER = False

    objects = UserManager()

    class Meta:
        ordering = ("email",)
        permissions = (
            (AccountPermissions.MANAGE_USERS.codename, "Manage customers."),
            (AccountPermissions.MANAGE_STAFF.codename, "Manage staff."),
            (AccountPermissions.IMPERSONATE_USER.codename, "Impersonate user."),
        )
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            # Orders searching index
            GinIndex(
                name="order_user_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["email", "first_name", "last_name"],
                opclasses=["gin_trgm_ops"] * 3,
            ),
            # Account searching index
            GinIndex(
                name="user_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["search_document"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="user_p_meta_jsonb_path_idx",
                fields=["private_metadata"],
                opclasses=["jsonb_path_ops"],
            ),
            GinIndex(
                fields=["first_name"],
                name="first_name_gin",
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                fields=["last_name"],
                name="last_name_gin",
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._effective_permissions = None

    def __str__(self):
        # Override the default __str__ of AbstractUser that returns username, which may
        # lead to leaking sensitive data in logs.
        return str(self.uuid)

    @property
    def effective_permissions(self) -> models.QuerySet[Permission]:
        """返回用户拥有的有效权限。

        这包括直接分配给用户的权限以及通过用户组分配的权限。
        超级用户拥有所有权限。

        Returns:
            QuerySet[Permission]: 用户拥有的权限查询集。
        """
        if self._effective_permissions is None:
            self._effective_permissions = get_permissions()
            if not self.is_superuser:
                UserPermission = User.user_permissions.through
                user_permission_queryset = UserPermission._default_manager.filter(
                    user_id=self.pk
                ).values("permission_id")

                UserGroup = User.groups.through
                GroupPermission = Group.permissions.through
                user_group_queryset = UserGroup._default_manager.filter(
                    user_id=self.pk
                ).values("group_id")
                group_permission_queryset = GroupPermission.objects.filter(
                    Exists(user_group_queryset.filter(group_id=OuterRef("group_id")))
                ).values("permission_id")

                self._effective_permissions = self._effective_permissions.filter(
                    Q(
                        Exists(
                            user_permission_queryset.filter(
                                permission_id=OuterRef("pk")
                            )
                        )
                    )
                    | Q(
                        Exists(
                            group_permission_queryset.filter(
                                permission_id=OuterRef("pk")
                            )
                        )
                    )
                )
        return self._effective_permissions

    @effective_permissions.setter
    def effective_permissions(self, value: models.QuerySet[Permission]):
        self._effective_permissions = value
        # Drop cache for authentication backend
        self._effective_permissions_cache = None

    def get_full_name(self):
        """返回用户的全名。

        如果设置了名字或姓氏，则返回它们的组合。
        否则，尝试从默认账单地址获取。
        如果仍然没有，则返回用户的电子邮件地址。

        Returns:
            str: 用户的全名。
        """
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        if self.default_billing_address:
            first_name = self.default_billing_address.first_name
            last_name = self.default_billing_address.last_name
            if first_name or last_name:
                return f"{first_name} {last_name}".strip()
        return self.email

    def get_short_name(self):
        """返回用户的简称（电子邮件地址）。

        Returns:
            str: 用户的电子邮件地址。
        """
        return self.email

    def has_perm(self, perm: BasePermissionEnum | str, obj=None) -> bool:
        """检查用户是否具有指定的权限。

        此方法被重写以接受 BasePermissionEnum 类型的权限。
        活动的超级用户拥有所有权限。

        Args:
            perm (BasePermissionEnum | str): 要检查的权限。
            obj (Any, optional): 检查对象权限的上下文。默认为 None。

        Returns:
            bool: 如果用户具有权限，则为 True，否则为 False。
        """
        # This method is overridden to accept perm as BasePermissionEnum
        perm = perm.value if isinstance(perm, BasePermissionEnum) else perm

        # Active superusers have all permissions.
        if self.is_active and self.is_superuser and not self._effective_permissions:
            return True
        return _user_has_perm(self, perm, obj)

    def has_perms(
        self, perm_list: Iterable[BasePermissionEnum | str], obj=None
    ) -> bool:
        """检查用户是否具有指定的权限列表中的所有权限。

        此方法被重写以接受 BasePermissionEnum 类型的权限。

        Args:
            perm_list (Iterable[BasePermissionEnum | str]): 要检查的权限列表。
            obj (Any, optional): 检查对象权限的上下文。默认为 None。

        Returns:
            bool: 如果用户具有所有权限，则为 True，否则为 False。
        """
        # This method is overridden to accept perm as BasePermissionEnum
        perm_list = [
            perm.value if isinstance(perm, BasePermissionEnum) else perm
            for perm in perm_list
        ]
        return super().has_perms(perm_list, obj)

    def can_login(self, site_settings: SiteSettings):
        """检查用户是否可以登录。

        Args:
            site_settings (SiteSettings): 当前的站点设置。

        Returns:
            bool: 如果用户可以登录，则为 True，否则为 False。
        """
        return self.is_active and (
            site_settings.allow_login_without_confirmation
            or not site_settings.enable_account_confirmation_by_email
            or self.is_confirmed
        )


class CustomerNote(models.Model):
    """关于客户的备注。

    Attributes:
        user (User): 创建此备注的用户（员工）。
        date (datetime): 备注的创建日期。
        content (str): 备注的内容。
        is_public (bool): 备注是否对客户可见。
        customer (User): 此备注所属的客户。
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL
    )
    date = models.DateTimeField(db_index=True, auto_now_add=True)
    content = models.TextField()
    is_public = models.BooleanField(default=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="notes", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("date",)


class CustomerEvent(models.Model):
    """用于存储客户生命周期中发生的事件的模型。

    Attributes:
        date (datetime): 事件发生的日期。
        type (str): 事件的类型。
        order (Order): 与事件相关的订单。
        parameters (dict): 与事件相关的参数。
        user (User): 与事件相关的用户。
        app (App): 创建此事件的应用。
    """

    date = models.DateTimeField(default=timezone.now, editable=False)
    type = models.CharField(
        max_length=255,
        choices=[
            (type_name.upper(), type_name) for type_name, _ in CustomerEvents.CHOICES
        ],
    )
    order = models.ForeignKey("order.Order", on_delete=models.SET_NULL, null=True)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        User, related_name="events", on_delete=models.CASCADE, null=True
    )
    app = models.ForeignKey(App, related_name="+", on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ("date",)

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"


class StaffNotificationRecipient(models.Model):
    """员工通知接收者模型。

    用于确定哪些员工应该接收有关商店事件的通知。

    Attributes:
        user (User): 关联的员工用户。
        staff_email (str): 员工的电子邮件地址（如果未关联用户）。
        active (bool): 此接收者是否处于活动状态。
    """

    user = models.OneToOneField(
        User,
        related_name="staff_notification",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    staff_email = models.EmailField(unique=True, blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("staff_email",)

    def get_email(self):
        """返回此接收者的电子邮件地址。

        如果有关联的用户，则返回用户的电子邮件地址，否则返回 `staff_email` 字段。

        Returns:
            str: 电子邮件地址。
        """
        return self.user.email if self.user else self.staff_email


class GroupManager(models.Manager):
    """auth 的 Group 模型的管理器。

    提供 `get_by_natural_key` 方法，以便在 fixtures 中按名称引用组。
    """

    use_in_migrations = True

    def get_by_natural_key(self, name):
        """通过自然键（名称）获取组。

        Args:
            name (str): 组的名称。

        Returns:
            Group: 具有给定名称的组实例。
        """
        return self.get(name=name)


class Group(models.Model):
    """系统提供了一种对用户进行分组的方式。

    组是一种通用的方式，用于对用户进行分类以应用权限或某些其他标签。
    一个用户可以属于任意数量的组。

    组中的用户自动拥有授予该组的所有权限。例如，如果“站点编辑”组
    具有 can_edit_home_page 权限，则该组中的任何用户都将拥有该权限。

    除了权限之外，组也是一种方便的方式，可以对用户进行分类以应用某些标签或
    扩展功能。例如，您可以创建一个“特殊用户”组，然后编写代码对这些用户
    执行特殊操作——例如让他们访问您网站的仅限会员部分，或向他们发送仅限
    会员的电子邮件消息。

    Attributes:
        name (str): 组的名称。
        permissions (ManyToManyField): 分配给该组的权限。
        restricted_access_to_channels (bool): 是否限制对渠道的访问。
        channels (ManyToManyField): 该组有权访问的渠道。
    """

    name = models.CharField("name", max_length=150, unique=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name="permissions",
        blank=True,
    )
    restricted_access_to_channels = models.BooleanField(default=False)
    channels = models.ManyToManyField("channel.Channel", blank=True)

    objects = GroupManager()

    class Meta:
        verbose_name = "group"
        verbose_name_plural = "groups"

    def __str__(self):
        return self.name

    def natural_key(self):
        """返回组的自然键（名称）。

        Returns:
            tuple: 包含组名称的元组。
        """
        return (self.name,)
