import graphene

from ...core.models import ModelWithMetadata
from ..channel import ChannelContext
from .resolvers import (
    resolve_metadata,
    resolve_object_with_metadata_type,
    resolve_private_metadata,
)


class MetadataItem(graphene.ObjectType):
    key = graphene.String(required=True, description="Key of a metadata item.")
    value = graphene.String(required=True, description="Value of a metadata item.")


class ObjectWithMetadata(graphene.Interface):
    private_metadata = graphene.List(
        MetadataItem,
        required=True,
        description=(
            "List of private metadata items."
            "Requires proper staff permissions to access."
        ),
    )
    metadata = graphene.List(
        MetadataItem,
        required=True,
        description=(
            "List of public metadata items. Can be accessed without permissions."
        ),
    )

    @staticmethod
    def resolve_metadata(root: ModelWithMetadata, _info):
        return resolve_metadata(root.metadata)

    @staticmethod
    def resolve_private_metadata(root: ModelWithMetadata, info):
        return resolve_private_metadata(root, info)

    @classmethod
    def resolve_type(cls, instance: ModelWithMetadata, _info):
        if isinstance(instance, ChannelContext):
            # Return instance for types that use ChannelContext
            instance = instance.node
        return resolve_object_with_metadata_type(instance)
