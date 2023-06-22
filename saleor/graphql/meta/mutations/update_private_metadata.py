import graphene

from ...core import ResolveInfo
from ...core.types import MetadataError, NonNullList
from ..inputs import MetadataInput
from ..permissions import PRIVATE_META_PERMISSION_MAP
from ..types import get_valid_metadata_instance
from .base import BaseMetadataMutation
from .utils import save_instance


class UpdatePrivateMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Updates private metadata of an object. To use it, you need to be an "
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
            cls.validate_metadata_keys(metadata_list)
            items = {data.key: data.value for data in metadata_list}
            meta_instance.store_value_in_private_metadata(items=items)
            save_instance(meta_instance, "private_metadata")
        return cls.success_response(instance)
