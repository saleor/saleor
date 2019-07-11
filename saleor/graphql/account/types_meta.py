import graphene


class MetaItem(graphene.ObjectType):
    key = graphene.String(required=True, description="Key for stored data.")
    value = graphene.String(required=True, description="Stored metadata value.")


class MetaClientStore(graphene.ObjectType):
    name = graphene.String(required=True, description="Metadata clients name.")
    metadata = graphene.List(MetaItem, description="Metadata stored for a client.")


class MetaStore(graphene.ObjectType):
    label = graphene.String(required=True, description="Name of metadata client group.")
    clients = graphene.List(
        MetaClientStore, description="List of clients that stored metadata in a group."
    )
