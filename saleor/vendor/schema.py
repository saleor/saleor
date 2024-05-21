import graphene
import json
from datetime import datetime


class User(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    last_login = graphene.DateTime(required=False)


class Query(graphene.ObjectType):
    user = graphene.List(User, first=graphene.Int())

    def resolve_user(self, info, first):
        return [
            User(username="Aleem", last_login=datetime.now()),
            User(username="Saad", last_login=datetime.now()),
            User(username="David", last_login=datetime.now()),
            User(username="Pedro", last_login=datetime.now()),
        ][:first]


class CreateUser(graphene.Mutation):
    user = graphene.Field(User)

    class Arguments:
        username = graphene.String()

    def mutate(self, info, username):
        user = User(username=username)
        return CreateUser(user=user)


class Mutations(graphene.ObjectType):
    create_user = CreateUser.Field()


schema = graphene.Schema(query=Query, mutation=Mutations)


result = schema.execute(
    """
    mutation mycreateUser {
        createUser(username: "Joshpe"){
            user {
                username,
                lastLogin
            }
        }
    }
    """
)
import pdb

print(result.data)
# pdb.set_trace()
# items = dict(result.data.items())
# print(json.dumps(items, indent=4))


# result = schema.execute(
#     """
#     {
#         user(first: 2) {
#             username,
#             lastLogin
#         }
#     }
#     """
# )
