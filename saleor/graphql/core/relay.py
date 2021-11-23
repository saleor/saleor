"""Implementation of Relay specification."""
import graphene


class NewPageInfo(graphene.ObjectType):
    has_next_page = graphene.Boolean(required=True)
    has_previous_page = graphene.Boolean(required=True)
    start_cursor = graphene.String()
    end_cursor = graphene.String()


class NewConnection(graphene.ObjectType):
    page_info = graphene.Field(NewPageInfo, required=True)
    total_count = graphene.Int()

    class Meta:
        abstract = True


types_registry = {}


def connection_field(graphql_type):
    type_name = get_type_name(graphql_type)
    if type_name not in types_registry:
        connection_type = create_connection_type(type_name)
        types_registry[type_name] = connection_type
    return graphene.Field(types_registry[type_name])


def get_type_name(graphql_type):
    try:
        return graphql_type.Meta.name or graphql_type.__name__
    except AttributeError:
        return graphql_type.__name__


def create_connection_type(type_name: str):
    connection_type_name = f"{type_name}ConnectionType"
    return type(
        connection_type_name, (NewConnection,), {}
    )
