import graphene

from ...checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus, error_codes
from ..core.enums import to_enum

OrderCreateFromCheckoutErrorCode = graphene.Enum.from_enum(
    error_codes.OrderCreateFromCheckoutErrorCode
)

CheckoutChargeStatusEnum = to_enum(
    CheckoutChargeStatus, description=CheckoutChargeStatus.__doc__
)
CheckoutAuthorizeStatusEnum = to_enum(
    CheckoutAuthorizeStatus, description=CheckoutAuthorizeStatus.__doc__
)
