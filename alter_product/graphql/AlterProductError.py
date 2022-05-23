from saleor.graphql.core.types.common import Error
from .enums import AlterProductErrorCode


class ALterProductError(Error):
    code = AlterProductErrorCode(description="The error code.", required=True)
