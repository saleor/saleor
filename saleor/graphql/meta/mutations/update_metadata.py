from typing import cast

import graphene

from ....core import models
from ...core import ResolveInfo
from ...core.types import MetadataError, NonNullList
from ..inputs import MetadataInput, MetadataInputDescription
from ..permissions import PUBLIC_META_PERMISSION_MAP
from .base import BaseMetadataMutation
from .utils import get_valid_metadata_instance, update_metadata


class UpdateMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Updates metadata of an object."
            f"{MetadataInputDescription.PRIVATE_METADATA_INPUT}"
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
        cls, _root, info: ResolveInfo, /, *, id: str, input: list
    ):
        instance = cast(models.ModelWithMetadata, cls.get_instance(info, id=id))
        if instance:
            meta_instance = get_valid_metadata_instance(instance)
            cls.create_metadata_from_graphql_input(input, error_field_name="input")
            items = {data.key: data.value for data in input}
            update_metadata(meta_instance, items)

        return cls.success_response(instance)
