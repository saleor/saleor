import graphene

from ....graphql.core.types.common import Error
from . import enums

CelebrityErrorCode = graphene.Enum.from_enum(enums.CelebrityErrorCode)


class CelebrityError(Error):
    code = CelebrityErrorCode(description="The error code.", required=True)
