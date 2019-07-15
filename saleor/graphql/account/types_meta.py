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
        return [{"key": k, "value": v} for k, v in root["metadata"].items()]


class MetaStore(graphene.ObjectType):
    label = graphene.String(required=True, description="Name of metadata client group.")
    clients = graphene.List(
        MetaClientStore,
        required=True,
        description="List of clients that stored metadata in a group.",
    )

    @staticmethod
    def resolve_clients(root: dict, _info):
        return [
            {"name": key, "metadata": value} for key, value in root["metadata"].items()
        ]
