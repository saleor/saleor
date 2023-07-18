from typing import List, cast

import graphene

from ....core import models
from ...core import ResolveInfo
from ...core.types import MetadataError, NonNullList
from ..inputs import MetadataInput
from ..permissions import PUBLIC_META_PERMISSION_MAP
from .base import BaseMetadataMutation
from .utils import get_valid_metadata_instance, save_instance


class UpdateMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Updates metadata of an object. To use it, you need to have access to the "
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
        input = NonNullList(
            MetadataInput,
            description="Fields required to update the object's metadata.",
            required=True,
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input: List
    ):
        instance = cast(models.ModelWithMetadata, cls.get_instance(info, id=id))
        if instance:
            meta_instance = get_valid_metadata_instance(instance)
            cls.validate_metadata_keys(input)
            items = {data.key: data.value for data in input}
            meta_instance.store_value_in_metadata(items=items)
            save_instance(meta_instance, ["metadata"])

        return cls.success_response(instance)
