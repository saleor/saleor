import graphene
from saleor.graphql.meta.types import ObjectWithMetadata
from saleor.core.models import ModelWithMetadata
from saleor.graphql.json_meta.resolvers import resolve_json_metadata, \
    resolve_json_private_metadata


class ObjectWithJSONMetadata(ObjectWithMetadata):
    json_private_metadata = graphene.JSONString(required=True, description=(
            "JSON of private metadata items."
            "Requires proper staff permissions to access."
        ),)
    json_metadata = graphene.JSONString(required=True, description=(
            "JSON of metadata items."
            "Requires proper staff permissions to access."
        ),)

    @staticmethod
    def resolve_json_metadata(root: ModelWithMetadata, _info):
        return resolve_json_metadata(root.metadata)

    @staticmethod
    def resolve_json_private_metadata(root: ModelWithMetadata, info):
        return resolve_json_private_metadata(root, info)

    @classmethod
    def resolve_type(cls, instance: ModelWithMetadata, _info):
        return ObjectWithMetadata.resolve_type(ObjectWithMetadata, instance, _info)

