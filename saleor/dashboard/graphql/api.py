import graphene
import graphql_jwt
from graphene_django.debug import DjangoDebug


class Query(graphene.ObjectType):
    node = graphene.Node.Field()
    debug = graphene.Field(DjangoDebug, name='__debug')


class Mutations(graphene.ObjectType):
    token_create = graphql_jwt.ObtainJSONWebToken.Field()
    token_refresh = graphql_jwt.Refresh.Field()


schema = graphene.Schema(Query)
