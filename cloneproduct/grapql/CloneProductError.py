from saleor.graphql.core.types.common import Error
from .enums import CloneProductErrorCode

class CustomError(Error):
    code = CloneProductErrorCode(description="The error code.", required=True)
