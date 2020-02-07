from operator import itemgetter

from graphql_jwt.exceptions import PermissionDenied

from ...account import models as account_models
from ...checkout import models as checkout_models
from ...core.models import ModelWithMetadata
from ...order import models as order_models
from ...product import models as product_models
from ..utils import get_user_or_service_account_from_context
from .permissions import PRIVATE_META_PERMISSION_MAP


def resolve_object_with_metadata_type(instance: ModelWithMetadata):
    # Imports inside resolvers to avoid circular imports.
    from ..account import types as account_types
    from ..checkout import types as checkout_types
    from ..order import types as order_types
    from ..product import types as product_types

    if isinstance(instance, product_models.Attribute):
        return product_types.Attribute
    if isinstance(instance, product_models.Category):
        return product_types.Category
    if isinstance(instance, checkout_models.Checkout):
        return checkout_types.Checkout
    if isinstance(instance, product_models.Collection):
        return product_types.Collection
    if isinstance(instance, product_models.DigitalContent):
        return product_types.DigitalContent
    if isinstance(instance, order_models.Fulfillment):
        return order_types.Fulfillment
    if isinstance(instance, order_models.Order):
        return order_types.Order
    if isinstance(instance, product_models.Product):
        return product_types.Product
    if isinstance(instance, product_models.ProductType):
        return product_types.ProductType
    if isinstance(instance, product_models.ProductVariant):
        return product_types.ProductVariant
    if isinstance(instance, account_models.ServiceAccount):
        return account_types.ServiceAccount
    if isinstance(instance, account_models.User):
        return account_types.User
    return None


def resolve_metadata(metadata: dict):
    return sorted(
        [{"key": k, "value": v} for k, v in metadata.items()], key=itemgetter("key"),
    )


def resolve_private_metadata(root: ModelWithMetadata, info):
    item_type = resolve_object_with_metadata_type(root)
    if not item_type:
        raise PermissionDenied()

    get_required_permission = PRIVATE_META_PERMISSION_MAP[item_type.__name__]
    if not get_required_permission:
        raise PermissionDenied()

    required_permission = get_required_permission(info, root.pk)
    if not required_permission:
        raise PermissionDenied()

    requester = get_user_or_service_account_from_context(info.context)
    if not requester.has_perms(required_permission):
        raise PermissionDenied()

    return resolve_metadata(root.private_meta)
