import graphene

from ....graphql.core.federation import build_federated_schema
from .mutations import SocialLogin, SocialLoginByAccessToken, SocialLoginConfirm


class Mutations(graphene.ObjectType):
    social_login = SocialLogin.Field()
    social_login_confirm_mobile = SocialLoginByAccessToken.Field()
    social_login_confirm_web = SocialLoginConfirm.Field()


schema = build_federated_schema(mutation=Mutations)
