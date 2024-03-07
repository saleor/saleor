from typing import Any, Callable, Union

from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

from ...account import models as account_models
from ...account.error_codes import AccountErrorCode
from ...attribute import AttributeType
from ...attribute import models as attribute_models
from ...core.exceptions import PermissionDenied
from ...core.jwt import JWT_THIRDPARTY_ACCESS_TYPE
from ...payment.utils import payment_owned_by_user
from ...permission.enums import (
    AccountPermissions,
    AppPermission,
    BasePermissionEnum,
    ChannelPermissions,
    CheckoutPermissions,
    DiscountPermissions,
    GiftcardPermissions,
    MenuPermissions,
    OrderPermissions,
    PagePermissions,
    PageTypePermissions,
    PaymentPermissions,
    ProductPermissions,
    ProductTypePermissions,
    ShippingPermissions,
    SitePermissions,
)
from ...site import models as site_models
from ...warehouse import models as warehouse_models
from ..app.dataloaders import get_app_promise
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..core.utils import from_global_id_or_error


def no_permissions(_info: ResolveInfo, _object_pk: Any) -> list[BasePermissionEnum]:
    return []


def public_user_permissions(
    info: ResolveInfo, user_pk: int
) -> list[BasePermissionEnum]:
    """Resolve permission for access to public metadata for user.

    Customer have access to own public metadata.
    Staff user with `MANAGE_USERS` have access to customers public metadata.
    Staff user with `MANAGE_STAFF` have access to staff users public metadata.
    """
    database_connection_name = get_database_connection_name(info.context)
    user = (
        account_models.User.objects.using(database_connection_name)
        .filter(pk=user_pk)
        .first()
    )
    if not user:
        raise ValidationError(
            {
                "id": ValidationError(
                    "Couldn't resolve user.", code=AccountErrorCode.NOT_FOUND.value
                )
            }
        )
    if info.context.user and info.context.user.pk == user.pk:
        return []
    if user.is_staff:
        return [AccountPermissions.MANAGE_STAFF]
    return [AccountPermissions.MANAGE_USERS]


def private_user_permissions(
    info: ResolveInfo, user_pk: int
) -> list[BasePermissionEnum]:
    database_connection_name = get_database_connection_name(info.context)
    user = (
        account_models.User.objects.using(database_connection_name)
        .filter(pk=user_pk)
        .first()
    )
    if not user:
        raise PermissionDenied()
    if user.is_staff:
        return [AccountPermissions.MANAGE_STAFF]
    return [AccountPermissions.MANAGE_USERS]


def public_address_permissions(
    info: ResolveInfo, address_pk: int
) -> list[BasePermissionEnum]:
    """Resolve permission for access to public metadata for user addresses.

    Customer have access to the public metadata of their own addresses.
    Staff user with `MANAGE_USERS` have access to public metadata of customer
    addresses.
    Staff user with `MANAGE_STAFF` have access to public metadata of staff user
    addresses.
    For now, updating warehouse and shop addresses is forbidden.
    """
    database_connection_name = get_database_connection_name(info.context)
    address = (
        account_models.Address.objects.using(database_connection_name)
        .filter(pk=address_pk)
        .prefetch_related("user_addresses")
        .first()
    )
    if not address:
        raise ValidationError(
            {
                "id": ValidationError(
                    "Couldn't resolve address.", code=AccountErrorCode.NOT_FOUND.value
                )
            }
        )
    user = info.context.user
    # no permission is required when the requestor is the owner of the address
    if user and address.user_addresses.filter(id=user.id):
        return []
    staff_users = account_models.User.objects.filter(is_staff=True)

    if address.user_addresses.filter(Exists(staff_users.filter(id=OuterRef("id")))):
        return [AccountPermissions.MANAGE_STAFF]
    elif (
        warehouse_models.Warehouse.objects.using(database_connection_name)
        .filter(address_id=address.id)
        .exists()
    ):
        return [ProductPermissions.MANAGE_PRODUCTS]
    elif (
        site_models.SiteSettings.objects.using(database_connection_name)
        .filter(company_address_id=address.id)
        .exists()
    ):
        return [SitePermissions.MANAGE_SETTINGS]

    return [AccountPermissions.MANAGE_USERS]


def private_address_permissions(
    info: ResolveInfo, address_pk: int
) -> list[BasePermissionEnum]:
    database_connection_name = get_database_connection_name(info.context)
    address = (
        account_models.Address.objects.using(database_connection_name)
        .filter(pk=address_pk)
        .prefetch_related("user_addresses")
        .first()
    )
    if not address:
        raise ValidationError(
            {
                "id": ValidationError(
                    "Couldn't resolve address.", code=AccountErrorCode.NOT_FOUND.value
                )
            }
        )
    staff_users = account_models.User.objects.using(database_connection_name).filter(
        is_staff=True
    )
    if address.user_addresses.filter(Exists(staff_users.filter(id=OuterRef("id")))):
        return [AccountPermissions.MANAGE_STAFF]
    if (
        warehouse_models.Warehouse.objects.using(database_connection_name)
        .filter(address_id=address.id)
        .exists()
        or site_models.SiteSettings.objects.using(database_connection_name)
        .filter(company_address_id=address.id)
        .exists()
    ):
        raise PermissionDenied()
    return [AccountPermissions.MANAGE_USERS]


def product_permissions(
    _info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    return [ProductPermissions.MANAGE_PRODUCTS]


def product_type_permissions(
    _info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    return [ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES]


def order_permissions(_info: ResolveInfo, _object_pk: Any) -> list[BasePermissionEnum]:
    return [OrderPermissions.MANAGE_ORDERS]


def invoice_permissions(
    _info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    return [OrderPermissions.MANAGE_ORDERS]


def menu_permissions(_info: ResolveInfo, _object_pk: Any) -> list[BasePermissionEnum]:
    return [MenuPermissions.MANAGE_MENUS]


def app_permissions(info: ResolveInfo, object_pk: str) -> list[BasePermissionEnum]:
    auth_token = info.context.decoded_auth_token or {}
    app = get_app_promise(info.context).get()
    app_id: Union[str, int, None]
    if auth_token.get("type") == JWT_THIRDPARTY_ACCESS_TYPE:
        _, app_id = from_global_id_or_error(auth_token["app"], "App")
    else:
        app_id = app.id if app else None
    if app_id is not None and int(app_id) == int(object_pk):
        return []
    return [AppPermission.MANAGE_APPS]


def private_app_permssions(
    info: ResolveInfo, object_pk: str
) -> list[BasePermissionEnum]:
    app = get_app_promise(info.context).get()
    if app and app.pk == int(object_pk):
        return []
    return [AppPermission.MANAGE_APPS]


def channel_permissions(
    _info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    return [ChannelPermissions.MANAGE_CHANNELS]


def checkout_permissions(
    _info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    return [CheckoutPermissions.MANAGE_CHECKOUTS]


def page_permissions(_info: ResolveInfo, _object_pk: Any) -> list[BasePermissionEnum]:
    return [PagePermissions.MANAGE_PAGES]


def page_type_permissions(
    _info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    return [PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES]


def attribute_permissions(info: ResolveInfo, attribute_pk: int):
    database_connection_name = get_database_connection_name(info.context)
    attribute = attribute_models.Attribute.objects.using(database_connection_name).get(
        pk=attribute_pk
    )
    if attribute.type == AttributeType.PAGE_TYPE:
        return page_type_permissions(info, attribute_pk)
    else:
        return product_type_permissions(info, attribute_pk)


def shipping_permissions(
    _info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    return [ShippingPermissions.MANAGE_SHIPPING]


def discount_permissions(
    _info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    return [DiscountPermissions.MANAGE_DISCOUNTS]


def public_payment_permissions(
    info: ResolveInfo, payment_pk: int
) -> list[BasePermissionEnum]:
    database_connection_name = get_database_connection_name(info.context)
    context_user = info.context.user
    app = get_app_promise(info.context).get()
    if app or (context_user and context_user.is_staff):
        return [PaymentPermissions.HANDLE_PAYMENTS]
    if payment_owned_by_user(payment_pk, context_user, database_connection_name):
        return []
    raise PermissionDenied()


def private_payment_permissions(
    info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    app = get_app_promise(info.context).get()
    if app is not None or (info.context.user and info.context.user.is_staff):
        return [PaymentPermissions.HANDLE_PAYMENTS]
    raise PermissionDenied(permissions=[PaymentPermissions.HANDLE_PAYMENTS])


def gift_card_permissions(
    _info: ResolveInfo, _object_pk: Any
) -> list[BasePermissionEnum]:
    return [GiftcardPermissions.MANAGE_GIFT_CARD]


def tax_permissions(_info: ResolveInfo, _object_pk: int) -> list[BasePermissionEnum]:
    return [
        CheckoutPermissions.HANDLE_TAXES,
        CheckoutPermissions.MANAGE_TAXES,
    ]


def site_permissions(_info: ResolveInfo, _object_pk: Any) -> list[BasePermissionEnum]:
    return [SitePermissions.MANAGE_SETTINGS]


PUBLIC_META_PERMISSION_MAP: dict[
    str, Callable[[ResolveInfo, Any], list[BasePermissionEnum]]
] = {
    "Address": public_address_permissions,
    "App": app_permissions,
    "Attribute": attribute_permissions,
    "Category": product_permissions,
    "Channel": channel_permissions,
    "Checkout": no_permissions,
    "CheckoutLine": no_permissions,
    "Collection": product_permissions,
    "DigitalContent": product_permissions,
    "Fulfillment": order_permissions,
    "GiftCard": gift_card_permissions,
    "Invoice": invoice_permissions,
    "Menu": menu_permissions,
    "MenuItem": menu_permissions,
    "Order": no_permissions,
    "OrderLine": no_permissions,
    "Page": page_permissions,
    "PageType": page_type_permissions,
    "Payment": public_payment_permissions,
    "Promotion": discount_permissions,
    "TransactionItem": private_payment_permissions,
    "Product": product_permissions,
    "ProductMedia": product_permissions,
    "ProductType": product_type_permissions,
    "ProductVariant": product_permissions,
    "Sale": discount_permissions,
    "ShippingMethodType": shipping_permissions,
    "ShippingZone": shipping_permissions,
    "Shop": site_permissions,
    "TaxConfiguration": tax_permissions,
    "TaxClass": tax_permissions,
    "User": public_user_permissions,
    "Voucher": discount_permissions,
    "Warehouse": product_permissions,
}


PRIVATE_META_PERMISSION_MAP: dict[
    str, Callable[[ResolveInfo, Any], list[BasePermissionEnum]]
] = {
    "Address": private_address_permissions,
    "App": private_app_permssions,
    "Attribute": attribute_permissions,
    "Category": product_permissions,
    "Channel": channel_permissions,
    "Checkout": checkout_permissions,
    "CheckoutLine": checkout_permissions,
    "Collection": product_permissions,
    "DigitalContent": product_permissions,
    "Fulfillment": order_permissions,
    "GiftCard": gift_card_permissions,
    "Invoice": invoice_permissions,
    "Menu": menu_permissions,
    "MenuItem": menu_permissions,
    "Order": order_permissions,
    "OrderLine": order_permissions,
    "Page": page_permissions,
    "PageType": page_type_permissions,
    "Payment": private_payment_permissions,
    "Promotion": discount_permissions,
    "TransactionItem": private_payment_permissions,
    "Product": product_permissions,
    "ProductMedia": product_permissions,
    "ProductType": product_type_permissions,
    "ProductVariant": product_permissions,
    "Sale": discount_permissions,
    "ShippingMethod": shipping_permissions,
    "ShippingMethodType": shipping_permissions,
    "ShippingZone": shipping_permissions,
    "Shop": site_permissions,
    "TaxConfiguration": tax_permissions,
    "TaxClass": tax_permissions,
    "User": private_user_permissions,
    "Voucher": discount_permissions,
    "Warehouse": product_permissions,
}
