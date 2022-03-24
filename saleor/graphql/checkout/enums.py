import graphene

from ...checkout import error_codes

OrderFromCheckoutCreateErrorCode = graphene.Enum.from_enum(
    error_codes.OrderFromCheckoutCreateErrorCode
)
