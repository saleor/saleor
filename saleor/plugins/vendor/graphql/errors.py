import graphene

from saleor.graphql.core.types.common import Error

from . import enums

AppErrorCode = graphene.Enum.from_enum(enums.VendorErrorCode)
AppErrorCodeBilling = graphene.Enum.from_enum(enums.BillingErrorCode)


class VendorError(Error):
    code = AppErrorCode(description="The error code.", required=True)


class BillingError(Error):
    code = AppErrorCodeBilling(description="The error code.", required=True)
