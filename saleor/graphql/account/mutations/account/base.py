import graphene

from ....core.enums import LanguageCodeEnum
from ....core.types import BaseInputObjectType


class AccountBaseInput(BaseInputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    language_code = graphene.Argument(
        LanguageCodeEnum, required=False, description="User language code."
    )
