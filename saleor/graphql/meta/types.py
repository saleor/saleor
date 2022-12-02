import graphene
from graphene.types.generic import GenericScalar

from ...core.models import ModelWithMetadata
from ..channel import ChannelContext
from ..core.descriptions import ADDED_IN_33, PREVIEW_FEATURE
from ..core.types import NonNullList
from .resolvers import (
    check_private_metadata_privilege,
    resolve_metadata,
    resolve_object_with_metadata_type,
    resolve_private_metadata,
)


class MetadataItem(graphene.ObjectType):
    key = graphene.String(required=True, description="Key of a metadata item.")
    value = graphene.String(required=True, description="Value of a metadata item.")


class Metadata(GenericScalar):
    """Metadata is a map of key-value pairs, both keys and values are `String`.

    Example:
    ```
    {
        "key1": "value1",
        "key2": "value2"
    }
    ```

    """


def _filter_metadata(metadata, keys):
    if keys is None:
        return metadata
    return {key: value for key, value in metadata.items() if key in keys}


class ObjectWithMetadata(graphene.Interface):
    private_metadata = NonNullList(
        MetadataItem,
        required=True,
        description=(
            "List of private metadata items. Requires staff permissions to access."
        ),
    )
    private_metafield = graphene.String(
        args={"key": graphene.NonNull(graphene.String)},
        description=(
            "A single key from private metadata. "
            "Requires staff permissions to access.\n\n"
            "Tip: Use GraphQL aliases to fetch multiple keys."
            + ADDED_IN_33
            + PREVIEW_FEATURE
        ),
    )
    private_metafields = Metadata(
        args={"keys": NonNullList(graphene.String)},
        description=(
            "Private metadata. Requires staff permissions to access. "
            "Use `keys` to control which fields you want to include. "
            "The default is to include everything." + ADDED_IN_33 + PREVIEW_FEATURE
        ),
    )
    metadata = NonNullList(
        MetadataItem,
        required=True,
        description=(
            "List of public metadata items. Can be accessed without permissions."
        ),
    )
    metafield = graphene.String(
        args={"key": graphene.NonNull(graphene.String)},
        description=(
            "A single key from public metadata.\n\n"
            "Tip: Use GraphQL aliases to fetch multiple keys."
            + ADDED_IN_33
            + PREVIEW_FEATURE
        ),
    )
    metafields = Metadata(
        args={"keys": NonNullList(graphene.String)},
        description=(
            "Public metadata. Use `keys` to control which fields you want to include. "
            "The default is to include everything." + ADDED_IN_33 + PREVIEW_FEATURE
        ),
    )

    @staticmethod
    def resolve_metadata(root: ModelWithMetadata, _info):
        return resolve_metadata(root.metadata)

    @staticmethod
    def resolve_metafield(root: ModelWithMetadata, _info, *, key: str):
        return root.metadata.get(key)

    @staticmethod
    def resolve_metafields(root: ModelWithMetadata, _info, *, keys=None):
        return _filter_metadata(root.metadata, keys)

    @staticmethod
    def resolve_private_metadata(root: ModelWithMetadata, info):
        return resolve_private_metadata(root, info)

    @staticmethod
    def resolve_private_metafield(root: ModelWithMetadata, info, *, key: str):
        check_private_metadata_privilege(root, info)
        return root.private_metadata.get(key)

    @staticmethod
    def resolve_private_metafields(root: ModelWithMetadata, info, *, keys=None):
        check_private_metadata_privilege(root, info)
        return _filter_metadata(root.private_metadata, keys)

    @classmethod
    def resolve_type(cls, instance: ModelWithMetadata, _info):
        if isinstance(instance, ChannelContext):
            # Return instance for types that use ChannelContext
            instance = instance.node
        item_type, _ = resolve_object_with_metadata_type(instance)
        return item_type
