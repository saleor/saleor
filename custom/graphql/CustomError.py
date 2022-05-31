from saleor.graphql.core.types.common import Error
from .enums import CustomErrorCode


class CustomError(Error):
    code = CustomErrorCode(description="The error code.", required=True)
