# Deprecated we should remove it in #5221
import graphene

from ..resolvers import resolve_metadata


class MetaItem(graphene.ObjectType):
    key = graphene.String(required=True, description="Key of a metadata item.")
    value = graphene.String(required=True, description="Value of a metadata item.")


class MetaPath(graphene.InputObjectType):
    namespace = graphene.String(
        required=True, description="Name of metadata client group.",
    )
    client_name = graphene.String(required=True, description="Metadata client's name.",)
    key = graphene.String(required=True, description="Key for stored data.")


class MetaInput(MetaPath):
    value = graphene.String(required=True, description="Stored metadata value.")


class MetaClientStore(graphene.ObjectType):
    name = graphene.String(required=True, description="Metadata client's name.")
    metadata = graphene.List(
        MetaItem, required=True, description="Metadata stored for a client."
    )

    @staticmethod
    def resolve_metadata(root, _info):
        return resolve_metadata(root)

    @staticmethod
    def resolve_name(_root, _info):
        return ""


class MetaStore(graphene.ObjectType):
    namespace = graphene.String(
        required=True, description="Name of metadata client group."
    )
    clients = graphene.List(
        MetaClientStore,
        required=True,
        description="List of clients that stored metadata in a group.",
    )

    @staticmethod
    def resolve_clients(root: dict, _info):
        if root:
            return [root]
        return []

    @staticmethod
    def resolve_namespace(_root, _info):
        return ""
