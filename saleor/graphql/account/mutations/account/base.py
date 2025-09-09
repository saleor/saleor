import graphene

from ....core.enums import LanguageCodeEnum


class AccountBaseInput(graphene.InputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    language_code = graphene.Argument(
        LanguageCodeEnum, required=False, description="User language code."
    )
