import graphene

from ...checkout import error_codes

OrderCreateFromCheckoutErrorCode = graphene.Enum.from_enum(
    error_codes.OrderCreateFromCheckoutErrorCode
)
