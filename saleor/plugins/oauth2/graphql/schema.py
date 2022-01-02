import graphene

from .mutations import SocialLogin, SocialLoginConfirm


class Queries(graphene.ObjectType):
    author = graphene.String(default_value="wecre8")


class Mutations(graphene.ObjectType):
    social_login = SocialLogin.Field()
    social_login_confirm = SocialLoginConfirm.Field()
    # account_register_social = AccountRegisterSocial.Field()


schema = graphene.Schema(query=Queries, mutation=Mutations)
