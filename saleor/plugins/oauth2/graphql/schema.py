import graphene
from graphene import ObjectType, Schema

from .mutations import InitateOAuth2Mutation, OAuth2CallbackMutation


class Query(ObjectType):
    author = graphene.String(default_value="wecre8")


class Mutations(ObjectType):
    iniate_oauth2 = InitateOAuth2Mutation.Field()
    oauth2_callback = OAuth2CallbackMutation.Field()


schema = Schema(query=Query, mutation=Mutations)
