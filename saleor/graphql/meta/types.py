import graphene

from ...core.models import ModelWithMetadata
from .resolvers import (
    resolve_metadata,
    resolve_object_with_metadata_type,
    resolve_private_metadata,
)


class MetaItem(graphene.ObjectType):
    key = graphene.String(required=True, description="Key for stored data.")
    value = graphene.String(required=True, description="Stored metadata value.")


class ObjectWithMetadata(graphene.Interface):
    private_metadata = graphene.List(
        MetaItem,
        required=True,
        description="List of publicly stored metadata namespaces.",
    )
    metadata = graphene.List(
        MetaItem,
        required=True,
        description="List of publicly stored metadata namespaces.",
    )

    # Deprecated we should remove it in #5221
    private_meta = graphene.List(
        "saleor.graphql.meta.deprecated.types.MetaStore",
        required=True,
        description="List of privately stored metadata namespaces.",
        deprecation_reason="DEPRECATED: Will be removed in Saleor 2.11. "
        "use the `privetaMetadata` field instead. ",
    )
    meta = graphene.List(
        "saleor.graphql.meta.deprecated.types.MetaStore",
        required=True,
        description="List of publicly stored metadata namespaces.",
        deprecation_reason="DEPRECATED: Will be removed in Saleor 2.11. "
        "use the `metadata` field instead. ",
    )

    @staticmethod
    def resolve_metadata(root: ModelWithMetadata, _info):
        return resolve_metadata(root.meta)

    @staticmethod
    def resolve_private_metadata(root: ModelWithMetadata, info):
        return resolve_private_metadata(root, info)

    @classmethod
    def resolve_type(cls, instance: ModelWithMetadata, _info):
        return resolve_object_with_metadata_type(instance)
