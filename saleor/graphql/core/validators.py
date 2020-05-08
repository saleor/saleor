from graphql.error import GraphQLError


def validate_query_args(**kwargs):
    id = kwargs.get("id")
    slug = kwargs.get("slug")
    name = kwargs.get("name")

    if id and slug:
        raise GraphQLError("Argument 'id' cannot be combined with 'slug'")
    if id and name:
        raise GraphQLError("Argument 'id' cannot be combined with 'name'")
