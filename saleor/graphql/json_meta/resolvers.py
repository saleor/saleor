from saleor.graphql.meta.resolvers import resolve_object_with_metadata_type
from saleor.graphql.meta.permissions import PRIVATE_META_PERMISSION_MAP
from ...core.exceptions import PermissionDenied
from ...core.models import ModelWithMetadata
from ..utils import get_user_or_app_from_context

def resolve_json_metadata(metadata: dict):
    return metadata

def resolve_json_private_metadata(root: ModelWithMetadata, info):
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

    return resolve_json_metadata(root.private_metadata)
