from typing import cast

import graphene

from ....core import models
from ...core import ResolveInfo
from ...core.types import MetadataError, NonNullList
from ..permissions import PUBLIC_META_PERMISSION_MAP
from .base import BaseMetadataMutation
from .utils import delete_metadata_keys, get_valid_metadata_instance


class DeleteMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Delete metadata of an object. To use it, you need to have access to the "
            "modified object."
        )
        permission_map = PUBLIC_META_PERMISSION_MAP
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
        instance = cast(models.ModelWithMetadata, cls.get_instance(info, id=id))
        if instance:
            meta_instance = get_valid_metadata_instance(instance)
            delete_metadata_keys(meta_instance, keys)
        return cls.success_response(instance)
