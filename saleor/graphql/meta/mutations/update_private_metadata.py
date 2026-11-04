from ...core import ResolveInfo
from ...core.types import MetadataError, NonNullList
from ..inputs import MetadataInput, MetadataInputDescription
from ..permissions import PRIVATE_META_PERMISSION_MAP
from .base import (
    BaseMetadataMutation,
    external_reference_argument,
    external_reference_type_argument,
    object_id_argument,
)
from .utils import get_valid_metadata_instance, update_private_metadata


class UpdatePrivateMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Updates private metadata of an object. "
            f"{MetadataInputDescription.PRIVATE_METADATA_INPUT}"
        )
        permission_map = PRIVATE_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = object_id_argument()
        external_reference = external_reference_argument()
        type = external_reference_type_argument()
        input = NonNullList(
            MetadataInput,
            description="Fields required to update the object's metadata.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)

        if instance:
            meta_instance = get_valid_metadata_instance(instance)
            metadata_list = data.pop("input")

            cls.create_metadata_from_graphql_input(
                metadata_list, error_field_name="input"
            )

            items = {data.key: data.value for data in metadata_list}
            update_private_metadata(meta_instance, items)

        return cls.success_response(instance)
