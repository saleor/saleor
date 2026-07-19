import graphene

from ...core import ResolveInfo
from ...core.types import MetadataError, NonNullList
from ..permissions import PRIVATE_META_PERMISSION_MAP
from .base import BaseMetadataMutation
from .utils import delete_private_metadata_keys, get_valid_metadata_instance


class DeletePrivateMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Delete object's private metadata. To use it, you need to be an "
            "authenticated staff user or an app and have access to the modified object."
        )
        permission_map = PRIVATE_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(
            description="ID or token (for Order and Checkout) of an object to update.",
            required=True,
        )
        keys = NonNullList(
            graphene.String,
            description="Metadata keys to delete.",
            required=True,
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, keys: list[str]
    ):
        instance = cls.get_instance(info, id=id)

        if instance:
            meta_instance = get_valid_metadata_instance(instance)
            delete_private_metadata_keys(meta_instance, keys)
        return cls.success_response(instance)
