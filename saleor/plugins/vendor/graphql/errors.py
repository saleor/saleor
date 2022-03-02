import graphene

from ....graphql.core.types.common import Error

from . import enums

VendorErrorCode = graphene.Enum.from_enum(enums.VendorErrorCode)


class VendorError(Error):
    code = VendorErrorCode(description="The error code.", required=True)
