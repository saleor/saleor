import graphene

from ....graphql.core.types import Error
from .enums import OAuth2ErrorCode as OAuth2ErrorCodeEnum

OAuth2ErrorCode = graphene.Enum.from_enum(OAuth2ErrorCodeEnum)


class OAuth2Error(Error):
    code = OAuth2ErrorCode(description="The error code.", required=False)
