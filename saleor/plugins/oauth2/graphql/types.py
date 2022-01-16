import graphene

from ....graphql.core.types import Error
from . import enums

OAuth2ErrorCode = graphene.Enum.from_enum(enums.OAuth2ErrorCode)


class OAuth2Error(Error):
    code = OAuth2ErrorCode(description="The error code", required=True)


class ProviderEnum(graphene.Enum):
    GOOGLE = "google"
    FACEBOOK = "facebook"


class OAuth2Input(graphene.InputObjectType):
    provider = ProviderEnum(required=True, description="Provider name.")
    code = graphene.String(
        required=True, description="The authorization code provided by the service"
    )
    state = graphene.String(
        required=True, description="A string to maintain state in the service."
    )
    redirect_url = graphene.String(
        required=True, description="A url to redirect to after authorization is done."
    )
    channel = graphene.String(
        required=False,
        description="The channel which the user should recieve emails in.",
    )


class OAuth2TokenInput(graphene.InputObjectType):
    provider = ProviderEnum(required=True, description="Provider name.")
    code = graphene.String(required=True, description="Provider access token.")
