from typing import Any, List

from django.core.exceptions import ValidationError

from ...account import models as account_models
from ...account.error_codes import AccountErrorCode
from ...attribute import AttributeType
from ...attribute import models as attribute_models
from ...core.exceptions import PermissionDenied
from ...core.jwt import JWT_THIRDPARTY_ACCESS_TYPE
from ...core.permissions import (
    AccountPermissions,
    AppPermission,
    BasePermissionEnum,
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
)
from ...payment.utils import payment_owned_by_user
from ..app.dataloaders import load_app
from ..core.utils import from_global_id_or_error


def no_permissions(_info, _object_pk: Any) -> List[None]:
    return []


def public_user_permissions(info, user_pk: int) -> List[BasePermissionEnum]:
    """Resolve permission for access to public metadata for user.

    Customer have access to own public metadata.
    Staff user with `MANAGE_USERS` have access to customers public metadata.
    Staff user with `MANAGE_STAFF` have access to staff users public metadata.
    """
    user = account_models.User.objects.filter(pk=user_pk).first()
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


def private_user_permissions(_info, user_pk: int) -> List[BasePermissionEnum]:
    user = account_models.User.objects.filter(pk=user_pk).first()
    if not user:
        raise PermissionDenied()
    if user.is_staff:
        return [AccountPermissions.MANAGE_STAFF]
    return [AccountPermissions.MANAGE_USERS]


def product_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [ProductPermissions.MANAGE_PRODUCTS]


def product_type_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES]


def order_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [OrderPermissions.MANAGE_ORDERS]


def invoice_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [OrderPermissions.MANAGE_ORDERS]


def menu_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [MenuPermissions.MANAGE_MENUS]


def app_permissions(info, object_pk: str) -> List[BasePermissionEnum]:
    auth_token = info.context.decoded_auth_token or {}
    app = load_app(info.context)
    if auth_token.get("type") == JWT_THIRDPARTY_ACCESS_TYPE:
        _, app_id = from_global_id_or_error(auth_token["app"], "App")
    else:
        app_id = app.id if app else None
    if app_id is not None and int(app_id) == int(object_pk):
        return []
    return [AppPermission.MANAGE_APPS]


def private_app_permssions(info, object_pk: str) -> List[BasePermissionEnum]:
    app = load_app(info.context)
    if app and app.pk == int(object_pk):
        return []
    return [AppPermission.MANAGE_APPS]


def checkout_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [CheckoutPermissions.MANAGE_CHECKOUTS]


def page_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [PagePermissions.MANAGE_PAGES]


def page_type_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES]


def attribute_permissions(_info, attribute_pk: int):
    attribute = attribute_models.Attribute.objects.get(pk=attribute_pk)
    if attribute.type == AttributeType.PAGE_TYPE:
        return page_type_permissions(_info, attribute_pk)
    else:
        return product_type_permissions(_info, attribute_pk)


def shipping_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [ShippingPermissions.MANAGE_SHIPPING]


def discount_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [DiscountPermissions.MANAGE_DISCOUNTS]


def public_payment_permissions(info, payment_pk: int) -> List[BasePermissionEnum]:
    context_user = info.context.user
    app = load_app(info.context)
    if app or (context_user and context_user.is_staff):
        return [PaymentPermissions.HANDLE_PAYMENTS]
    if payment_owned_by_user(payment_pk, context_user):
        return []
    raise PermissionDenied()


def private_payment_permissions(info, _object_pk: Any) -> List[BasePermissionEnum]:
    app = load_app(info.context)
    if app is not None or info.context.user.is_staff:
        return [PaymentPermissions.HANDLE_PAYMENTS]
    raise PermissionDenied(permissions=[PaymentPermissions.HANDLE_PAYMENTS])


def gift_card_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [GiftcardPermissions.MANAGE_GIFT_CARD]


def tax_permissions(_info, _object_pk: int) -> List[BasePermissionEnum]:
    return [
        CheckoutPermissions.HANDLE_TAXES,
        CheckoutPermissions.MANAGE_TAXES,
    ]


PUBLIC_META_PERMISSION_MAP = {
    "App": app_permissions,
    "Attribute": attribute_permissions,
    "Category": product_permissions,
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
    "TransactionItem": private_payment_permissions,
    "Product": product_permissions,
    "ProductType": product_type_permissions,
    "ProductVariant": product_permissions,
    "Sale": discount_permissions,
    "ShippingMethodType": shipping_permissions,
    "ShippingZone": shipping_permissions,
    "TaxConfiguration": tax_permissions,
    "TaxClass": tax_permissions,
    "User": public_user_permissions,
    "Voucher": discount_permissions,
    "Warehouse": product_permissions,
}


PRIVATE_META_PERMISSION_MAP = {
    "App": private_app_permssions,
    "Attribute": attribute_permissions,
    "Category": product_permissions,
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
    "TransactionItem": private_payment_permissions,
    "Product": product_permissions,
    "ProductType": product_type_permissions,
    "ProductVariant": product_permissions,
    "Sale": discount_permissions,
    "ShippingMethod": shipping_permissions,
    "ShippingMethodType": shipping_permissions,
    "ShippingZone": shipping_permissions,
    "TaxConfiguration": tax_permissions,
    "TaxClass": tax_permissions,
    "User": private_user_permissions,
    "Voucher": discount_permissions,
    "Warehouse": product_permissions,
}
