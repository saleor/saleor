import dataclasses
from operator import itemgetter

from ...account import models as account_models
from ...app import models as app_models
from ...attribute import models as attribute_models
from ...checkout import models as checkout_models
from ...core.exceptions import PermissionDenied
from ...core.models import ModelWithMetadata
from ...discount import models as discount_models
from ...giftcard import models as giftcard_models
from ...order import models as order_models
from ...page import models as page_models
from ...payment import models as payment_models
from ...permission.utils import one_of_permissions_or_auth_filter_required
from ...product import models as product_models
from ...shipping import models as shipping_models
from ...shipping.interface import ShippingMethodData
from ...tax import models as tax_models
from ...warehouse import models as warehouse_models
from ..core import ResolveInfo
from ..utils import get_user_or_app_from_context
from .permissions import PRIVATE_META_PERMISSION_MAP


def resolve_object_with_metadata_type(instance):
    # Imports inside resolvers to avoid circular imports.
    from ...invoice import models as invoice_models
    from ...menu import models as menu_models
    from ..account import types as account_types
    from ..app import types as app_types
    from ..attribute import types as attribute_types
    from ..checkout import types as checkout_types
    from ..discount import types as discount_types
    from ..giftcard import types as giftcard_types
    from ..invoice import types as invoice_types
    from ..menu import types as menu_types
    from ..order import types as order_types
    from ..page import types as page_types
    from ..payment import types as payment_types
    from ..product import types as product_types
    from ..shipping import types as shipping_types
    from ..tax import types as tax_types
    from ..warehouse import types as warehouse_types

    if isinstance(instance, ModelWithMetadata):
        MODEL_TO_TYPE_MAP = {
            account_models.Address: account_types.Address,
            account_models.User: account_types.User,
            app_models.App: app_types.App,
            attribute_models.Attribute: attribute_types.Attribute,
            checkout_models.Checkout: checkout_types.Checkout,
            checkout_models.CheckoutMetadata: checkout_types.Checkout,
            checkout_models.CheckoutLine: checkout_types.CheckoutLine,
            discount_models.Sale: discount_types.Sale,
            discount_models.Voucher: discount_types.Voucher,
            giftcard_models.GiftCard: giftcard_types.GiftCard,
            invoice_models.Invoice: invoice_types.Invoice,
            menu_models.Menu: menu_types.Menu,
            menu_models.MenuItem: menu_types.MenuItem,
            order_models.Fulfillment: order_types.Fulfillment,
            order_models.Order: order_types.Order,
            order_models.OrderLine: order_types.OrderLine,
            page_models.Page: page_types.Page,
            page_models.PageType: page_types.PageType,
            payment_models.Payment: payment_types.Payment,
            payment_models.TransactionItem: payment_types.TransactionItem,
            product_models.Category: product_types.Category,
            product_models.Collection: product_types.Collection,
            product_models.DigitalContent: product_types.DigitalContent,
            product_models.Product: product_types.Product,
            product_models.ProductType: product_types.ProductType,
            product_models.ProductVariant: product_types.ProductVariant,
            shipping_models.ShippingMethod: shipping_types.ShippingMethodType,
            shipping_models.ShippingZone: shipping_types.ShippingZone,
            tax_models.TaxClass: tax_types.TaxClass,
            tax_models.TaxConfiguration: tax_types.TaxConfiguration,
            warehouse_models.Warehouse: warehouse_types.Warehouse,
        }
        return MODEL_TO_TYPE_MAP.get(instance.__class__, None), instance.pk

    elif dataclasses.is_dataclass(instance):
        DATACLASS_TO_TYPE_MAP = {ShippingMethodData: shipping_types.ShippingMethod}
        return DATACLASS_TO_TYPE_MAP.get(instance.__class__, None), instance.id
    raise ValueError(f"Unknown type: {instance.__class__}")


def resolve_metadata(metadata: dict):
    return sorted(
        [{"key": k, "value": v} for k, v in metadata.items()],
        key=itemgetter("key"),
    )


def check_private_metadata_privilege(root: ModelWithMetadata, info: ResolveInfo):
    item_type, item_id = resolve_object_with_metadata_type(root)
    if not item_type:
        raise NotImplementedError(
            f"Model {type(root)} can't be mapped to type with metadata. "
            "Make sure that model exists inside MODEL_TO_TYPE_MAP."
        )

    get_required_permission = PRIVATE_META_PERMISSION_MAP.get(item_type.__name__)
    if not get_required_permission:
        raise PermissionDenied()

    required_permissions = get_required_permission(info, item_id)

    if not isinstance(required_permissions, list):
        raise PermissionDenied()

    requester = get_user_or_app_from_context(info.context)
    if not requester or not one_of_permissions_or_auth_filter_required(
        info.context, required_permissions
    ):
        raise PermissionDenied()


def resolve_private_metadata(root: ModelWithMetadata, info: ResolveInfo):
    check_private_metadata_privilege(root, info)
    return resolve_metadata(root.private_metadata)
