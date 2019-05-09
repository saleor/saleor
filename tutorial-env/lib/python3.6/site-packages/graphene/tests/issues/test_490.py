# https://github.com/graphql-python/graphene/issues/313

import graphene


class Query(graphene.ObjectType):
    some_field = graphene.String(from_=graphene.String(name="from"))

    def resolve_some_field(self, info, from_=None):
        return from_


def test_issue():
    query_string = """
    query myQuery {
      someField(from: "Oh")
    }
    """

    schema = graphene.Schema(query=Query)
    result = schema.execute(query_string)

    assert not result.errors
    assert result.data["someField"] == "Oh"
