import graphene
from saleor.graphql.meta.resolvers import resolve_object_with_metadata_type

from saleor.core.models import ModelWithMetadata
from saleor.graphql.json_meta.resolvers import resolve_json_metadata, \
    resolve_json_private_metadata


class ObjectWithJSONMetadata(graphene.Interface):
    json_private_metadata = graphene.List(
        graphene.JSONString,
        required=True,
        description=(
            "List of private metadata items."
            "Requires proper staff permissions to access."
        ),
    )
    json_metadata = graphene.List(
        graphene.JSONString,
        required=True,
        description=(
            "List of public metadata items. Can be accessed without permissions."
        ),
    )

    @staticmethod
    def resolve_json_metadata(root: ModelWithMetadata, _info):
        return resolve_json_metadata(root.metadata)

    @staticmethod
    def resolve_json_private_metadata(root: ModelWithMetadata, info):
        return resolve_json_private_metadata(root, info)

    @classmethod
    def resolve_type(cls, instance: ModelWithMetadata, _info):
        return resolve_object_with_metadata_type(instance)

