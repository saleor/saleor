import graphene

from saleor.account import models
from saleor.graphql.account.types import UserCountableConnection
from saleor.graphql.core.connection import create_connection_slice
from saleor.graphql.core.fields import FilterConnectionField

from ....graphql.core.federation import build_federated_schema
from .mutations import SocialLogin, SocialLoginByAccessToken, SocialLoginConfirm


# test any query
class Query(graphene.ObjectType):
    customers2 = FilterConnectionField(
        UserCountableConnection,
        description="List of the shop's customers.",
    )

    def resolve_customers2(self, info, **kwargs):
        qs = models.User.objects.customers()
        return create_connection_slice(qs, info, kwargs, UserCountableConnection)


class Mutation(graphene.ObjectType):
    social_login = SocialLogin.Field()
    social_login_confirm_mobile = SocialLoginByAccessToken.Field()
    social_login_confirm_web = SocialLoginConfirm.Field()


schema = build_federated_schema(query=Query, mutation=Mutation)
