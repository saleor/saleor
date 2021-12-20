import graphene

from ....graphql.core.federation import build_federated_schema
from .mutations import InitateOAuth2Mutation, OAuth2CallbackMutation


class Queries(graphene.ObjectType):
    author = graphene.String(default_value="wecre8")


class Mutations(graphene.ObjectType):
    iniate_oauth2 = InitateOAuth2Mutation.Field()
    oauth2_callback = OAuth2CallbackMutation.Field()


schema = build_federated_schema(query=Queries, mutation=Mutations)
