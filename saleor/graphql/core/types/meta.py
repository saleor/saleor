from operator import itemgetter

from graphql_jwt.decorators import permission_required
import graphene


class MetaItem(graphene.ObjectType):
    key = graphene.String(required=True, description="Key for stored data.")
    value = graphene.String(required=True, description="Stored metadata value.")


class MetaClientStore(graphene.ObjectType):
    name = graphene.String(required=True, description="Metadata clients name.")
    metadata = graphene.List(
        MetaItem, required=True, description="Metadata stored for a client."
    )

    @staticmethod
    def resolve_metadata(root, _info):
        return sorted(
            [{"key": k, "value": v} for k, v in root["metadata"].items()],
            key=itemgetter("key"),
        )


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
        return sorted(
            [
                {"name": key, "metadata": value}
                for key, value in root["metadata"].items()
            ],
            key=itemgetter("name"),
        )


class MetaPath(graphene.InputObjectType):
    namespace = graphene.String(
        required=True, description="Name of metadata client group."
    )
    client_name = graphene.String(required=True, description="Metadata clients name.")
    key = graphene.String(required=True, description="Key for stored data.")


class MetaInput(MetaPath):
    value = graphene.String(required=True, description="Stored metadata value.")


class MetadataObjectType(graphene.ObjectType):
    private_meta = graphene.List(
        MetaStore,
        required=True,
        description="List of privately stored metadata namespaces.",
    )
    meta = graphene.List(
        MetaStore,
        required=True,
        description="List of publicly stored metadata namespaces.",
    )

    @staticmethod
    @permission_required("account.manage_users")
    def resolve_private_meta(root, _info):
        return sorted(
            [
                {"namespace": namespace, "metadata": data}
                for namespace, data in root.private_meta.items()
            ],
            key=itemgetter("namespace"),
        )

    @staticmethod
    def resolve_meta(root, _info):
        return sorted(
            [
                {"namespace": namespace, "metadata": data}
                for namespace, data in root.meta.items()
            ],
            key=itemgetter("namespace"),
        )
