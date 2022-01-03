import graphene

from .mutations import SocialLogin, SocialLoginByAccessToken, SocialLoginConfirm


class Mutations(graphene.ObjectType):
    social_login = SocialLogin.Field()
    social_login_confirm_mobile = SocialLoginByAccessToken.Field()
    social_login_confirm_web = SocialLoginConfirm.Field()


schema = graphene.Schema(mutation=Mutations)
