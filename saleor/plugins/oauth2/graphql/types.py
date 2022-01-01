import graphene

from ....graphql.core.enums import LanguageCodeEnum
from ....graphql.core.types import Error
from .enums import OAuth2ErrorCode as OAuth2ErrorCodeEnum

OAuth2ErrorCode = graphene.Enum.from_enum(OAuth2ErrorCodeEnum)


class OAuth2Error(Error):
    code = OAuth2ErrorCode(description="The error code", required=True)


class ProviderEnum(graphene.Enum):
    GOOGLE = "google"
    FACEBOOK = "facebook"


class OAuth2Input(graphene.InputObjectType):
    provider = ProviderEnum(required=True)
    code = graphene.String(required=True)
    state = graphene.String(required=True)
    redirect_url = graphene.String(required=True)
    channel = graphene.String(required=False)
    language_code = graphene.Field(
        LanguageCodeEnum,
        required=False,
        description="User language code.",
        default_value="AR",
    )
