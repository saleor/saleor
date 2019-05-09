# https://github.com/graphql-python/graphene/issues/313

import graphene


class Query(graphene.ObjectType):
    rand = graphene.String()


class Success(graphene.ObjectType):
    yeah = graphene.String()


class Error(graphene.ObjectType):
    message = graphene.String()


class CreatePostResult(graphene.Union):
    class Meta:
        types = [Success, Error]


class CreatePost(graphene.Mutation):
    class Input:
        text = graphene.String(required=True)

    result = graphene.Field(CreatePostResult)

    def mutate(self, info, text):
        result = Success(yeah="yeah")

        return CreatePost(result=result)


class Mutations(graphene.ObjectType):
    create_post = CreatePost.Field()


# tests.py


def test_create_post():
    query_string = """
    mutation {
      createPost(text: "Try this out") {
        result {
          __typename
        }
      }
    }
    """

    schema = graphene.Schema(query=Query, mutation=Mutations)
    result = schema.execute(query_string)

    assert not result.errors
    assert result.data["createPost"]["result"]["__typename"] == "Success"
