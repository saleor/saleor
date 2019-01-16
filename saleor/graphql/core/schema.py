import graphene
import graphql_jwt

from .mutations import CreateToken, VerifyToken


class CoreMutations(graphene.ObjectType):
    token_create = CreateToken.Field()
    token_refresh = graphql_jwt.Refresh.Field()
    token_verify = VerifyToken.Field()
