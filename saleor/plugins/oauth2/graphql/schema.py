import graphene

from ....graphql.core.federation import build_federated_schema
from .mutations import InitiateOAuth2Mutation, OAuth2CallbackMutation


class Queries(graphene.ObjectType):
    author = graphene.String(default_value="wecre8")


class Mutations(graphene.ObjectType):
    initiate_oauth2 = InitiateOAuth2Mutation.Field()
    oauth2_callback = OAuth2CallbackMutation.Field()


schema = build_federated_schema(query=Queries, mutation=Mutations)
