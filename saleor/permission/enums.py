from enum import Enum
from typing import Iterable, List

from django.db.models import QuerySet

from .models import Permission


class BasePermissionEnum(Enum):
    @property
    def codename(self):
        return self.value.split(".")[1]


class AccountPermissions(BasePermissionEnum):
    MANAGE_USERS = "account.manage_users"
    MANAGE_STAFF = "account.manage_staff"
    IMPERSONATE_USER = "account.impersonate_user"


class AppPermission(BasePermissionEnum):
    MANAGE_APPS = "app.manage_apps"
    MANAGE_OBSERVABILITY = "app.manage_observability"


class ChannelPermissions(BasePermissionEnum):
    MANAGE_CHANNELS = "channel.manage_channels"


class DiscountPermissions(BasePermissionEnum):
    MANAGE_DISCOUNTS = "discount.manage_discounts"


class PluginsPermissions(BasePermissionEnum):
    MANAGE_PLUGINS = "plugins.manage_plugins"


class GiftcardPermissions(BasePermissionEnum):
    MANAGE_GIFT_CARD = "giftcard.manage_gift_card"


class MenuPermissions(BasePermissionEnum):
    MANAGE_MENUS = "menu.manage_menus"


class CheckoutPermissions(BasePermissionEnum):
    MANAGE_CHECKOUTS = "checkout.manage_checkouts"
    HANDLE_CHECKOUTS = "checkout.handle_checkouts"
    HANDLE_TAXES = "checkout.handle_taxes"
    MANAGE_TAXES = "checkout.manage_taxes"


class OrderPermissions(BasePermissionEnum):
    MANAGE_ORDERS = "order.manage_orders"


class PaymentPermissions(BasePermissionEnum):
    HANDLE_PAYMENTS = "payment.handle_payments"


class PagePermissions(BasePermissionEnum):
    MANAGE_PAGES = "page.manage_pages"


class PageTypePermissions(BasePermissionEnum):
    MANAGE_PAGE_TYPES_AND_ATTRIBUTES = "page.manage_page_types_and_attributes"


class ProductPermissions(BasePermissionEnum):
    MANAGE_PRODUCTS = "product.manage_products"


class ProductTypePermissions(BasePermissionEnum):
    MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES = "product.manage_product_types_and_attributes"


class ShippingPermissions(BasePermissionEnum):
    MANAGE_SHIPPING = "shipping.manage_shipping"


class SitePermissions(BasePermissionEnum):
    MANAGE_SETTINGS = "site.manage_settings"
    MANAGE_TRANSLATIONS = "site.manage_translations"


PERMISSIONS_ENUMS = [
    AccountPermissions,
    AppPermission,
    CheckoutPermissions,
    ChannelPermissions,
    DiscountPermissions,
    GiftcardPermissions,
    MenuPermissions,
    OrderPermissions,
    PagePermissions,
    PageTypePermissions,
    PaymentPermissions,
    PluginsPermissions,
    ProductPermissions,
    ProductTypePermissions,
    ShippingPermissions,
    SitePermissions,
]


def get_permissions_codename():
    permissions_values = [
        enum.codename
        for permission_enum in PERMISSIONS_ENUMS
        for enum in permission_enum
    ]
    return permissions_values


def get_permissions_enum_list():
    permissions_list = [
        (enum.name, enum.value)
        for permission_enum in PERMISSIONS_ENUMS
        for enum in permission_enum
    ]
    return permissions_list


def get_permissions_enum_dict():
    return {
        enum.name: enum
        for permission_enum in PERMISSIONS_ENUMS
        for enum in permission_enum
    }


def get_permissions_from_names(names: List[str]):
    """Convert list of permission names - ['MANAGE_ORDERS'] to Permission db objects."""
    permissions = get_permissions_enum_dict()
    return get_permissions([permissions[name].value for name in names])


def get_permission_names(permissions: Iterable["Permission"]):
    """Convert Permissions db objects to list of Permission enums."""
    permission_dict = get_permissions_enum_dict()
    names = set()
    for perm in permissions:
        for _, perm_enum in permission_dict.items():
            if perm.codename == perm_enum.codename:
                names.add(perm_enum.name)
    return names


def split_permission_codename(permissions):
    return [permission.split(".")[1] for permission in permissions]


def get_permissions(permissions=None):
    if permissions is None:
        codenames = get_permissions_codename()
    else:
        codenames = split_permission_codename(permissions)
    return get_permissions_from_codenames(codenames)


def get_permissions_from_codenames(permission_codenames: List[str]) -> QuerySet:
    return (
        Permission.objects.filter(codename__in=permission_codenames)
        .prefetch_related("content_type")
        .order_by("codename")
    )
