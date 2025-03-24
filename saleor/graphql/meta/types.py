import graphene
from graphene.types.generic import GenericScalar

from ...core.models import ModelWithMetadata
from ..core import ResolveInfo
from ..core.context import BaseContext
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


def _get_metadata_instance(
    root: ModelWithMetadata | BaseContext[ModelWithMetadata],
) -> ModelWithMetadata:
    if isinstance(root, BaseContext):
        return root.node
    return root


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
        ),
    )
    private_metafields = Metadata(
        args={"keys": NonNullList(graphene.String)},
        description=(
            "Private metadata. Requires staff permissions to access. "
            "Use `keys` to control which fields you want to include. "
            "The default is to include everything."
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
        ),
    )
    metafields = Metadata(
        args={"keys": NonNullList(graphene.String)},
        description=(
            "Public metadata. Use `keys` to control which fields you want to include. "
            "The default is to include everything."
        ),
    )

    @staticmethod
    def resolve_metadata(
        root: ModelWithMetadata | BaseContext[ModelWithMetadata], _info: ResolveInfo
    ):
        instance = _get_metadata_instance(root)
        return resolve_metadata(instance.metadata)

    @staticmethod
    def resolve_metafield(
        root: ModelWithMetadata | BaseContext[ModelWithMetadata],
        _info: ResolveInfo,
        *,
        key: str,
    ) -> str | None:
        instance = _get_metadata_instance(root)
        return instance.metadata.get(key)

    @staticmethod
    def resolve_metafields(root: ModelWithMetadata, _info: ResolveInfo, *, keys=None):
        instance = _get_metadata_instance(root)
        return _filter_metadata(instance.metadata, keys)

    @staticmethod
    def resolve_private_metadata(
        root: ModelWithMetadata | BaseContext[ModelWithMetadata], info: ResolveInfo
    ):
        instance = _get_metadata_instance(root)
        return resolve_private_metadata(instance, info)

    @staticmethod
    def resolve_private_metafield(
        root: ModelWithMetadata | BaseContext[ModelWithMetadata],
        info: ResolveInfo,
        *,
        key: str,
    ) -> str | None:
        instance = _get_metadata_instance(root)
        check_private_metadata_privilege(instance, info)
        return instance.private_metadata.get(key)

    @staticmethod
    def resolve_private_metafields(
        root: ModelWithMetadata | BaseContext[ModelWithMetadata],
        info: ResolveInfo,
        *,
        keys=None,
    ):
        instance = _get_metadata_instance(root)
        check_private_metadata_privilege(instance, info)
        return _filter_metadata(instance.private_metadata, keys)

    @classmethod
    def resolve_type(
        cls,
        instance: ModelWithMetadata | BaseContext[ModelWithMetadata],
        info: ResolveInfo,
    ):
        instance = _get_metadata_instance(instance)
        item_type, _ = resolve_object_with_metadata_type(instance)
        return item_type
