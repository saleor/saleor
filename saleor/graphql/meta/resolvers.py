from operator import itemgetter

from graphql_jwt.exceptions import PermissionDenied

from ...account import models as account_models
from ...app import models as app_models
from ...checkout import models as checkout_models
from ...core.models import ModelWithMetadata
from ...order import models as order_models
from ...product import models as product_models
from ..utils import get_user_or_app_from_context
from .permissions import PRIVATE_META_PERMISSION_MAP


def resolve_object_with_metadata_type(instance: ModelWithMetadata):
    # Imports inside resolvers to avoid circular imports.
    from ..account import types as account_types
    from ..app import types as app_types
    from ..checkout import types as checkout_types
    from ..order import types as order_types
    from ..product import types as product_types

    MODEL_TO_TYPE_MAP = {
        product_models.Attribute: product_types.Attribute,
        product_models.Category: product_types.Category,
        checkout_models.Checkout: checkout_types.Checkout,
        product_models.Collection: product_types.Collection,
        product_models.DigitalContent: product_types.DigitalContent,
        order_models.Fulfillment: order_types.Fulfillment,
        order_models.Order: order_types.Order,
        product_models.Product: product_types.Product,
        product_models.ProductType: product_types.ProductType,
        product_models.ProductVariant: product_types.ProductVariant,
        app_models.App: app_types.App,
        account_models.User: account_types.User,
    }
    return MODEL_TO_TYPE_MAP.get(type(instance), None)


def resolve_metadata(metadata: dict):
    return sorted(
        [{"key": k, "value": v} for k, v in metadata.items()], key=itemgetter("key"),
    )


def resolve_private_metadata(root: ModelWithMetadata, info):
    item_type = resolve_object_with_metadata_type(root)
    if not item_type:
        raise NotImplementedError(
            f"Model {type(root)} can't be mapped to type with metadata. "
            "Make sure that model exists inside MODEL_TO_TYPE_MAP."
        )

    get_required_permission = PRIVATE_META_PERMISSION_MAP[item_type.__name__]
    if not get_required_permission:
        raise PermissionDenied()

    required_permission = get_required_permission(info, root.pk)
    if not required_permission:
        raise PermissionDenied()

    requester = get_user_or_app_from_context(info.context)
    if not requester.has_perms(required_permission):
        raise PermissionDenied()

    return resolve_metadata(root.private_metadata)
