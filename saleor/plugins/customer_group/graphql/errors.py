import graphene

from saleor.graphql.core.types.common import Error
from saleor.plugins.customer_group.graphql.enums import CustomerGroupErrorCode

AppErrorCode = graphene.Enum.from_enum(CustomerGroupErrorCode)


class CustomerGroupError(Error):
    code = AppErrorCode(description="The error code.", required=True)
