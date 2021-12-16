import graphene

from ....graphql.core.federation import build_federated_schema
from .mutations import RequestPasswordRecovery, SetPasswordByCode


class Queries(graphene.ObjectType):
    author = graphene.String(default_value="WeCre8")


class Mutations(graphene.ObjectType):
    request_password_recovery = RequestPasswordRecovery.Field()
    set_password_by_code = SetPasswordByCode.Field()


schema = build_federated_schema(query=Queries, mutation=Mutations)
