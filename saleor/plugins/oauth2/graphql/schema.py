import graphene

from .mutations import SocialLogin, SocialLoginByAccessToken, SocialLoginConfirm


class Queries(graphene.ObjectType):
    author = graphene.String(default_value="wecre8")


class Mutations(graphene.ObjectType):
    social_login = SocialLogin.Field()
    social_login_confirm_mobile = SocialLoginByAccessToken.Field()
    social_login_confirm_web = SocialLoginConfirm.Field()


schema = graphene.Schema(query=Queries, mutation=Mutations)
