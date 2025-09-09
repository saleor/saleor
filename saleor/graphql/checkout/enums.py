import graphene

from ...checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus, error_codes
from ..core.doc_category import DOC_CATEGORY_CHECKOUT, DOC_CATEGORY_ORDERS
from ..core.enums import to_enum
from ..directives import doc

OrderCreateFromCheckoutErrorCode = doc(
    DOC_CATEGORY_ORDERS,
    graphene.Enum.from_enum(error_codes.OrderCreateFromCheckoutErrorCode),
)

CheckoutChargeStatusEnum = doc(
    DOC_CATEGORY_CHECKOUT,
    to_enum(CheckoutChargeStatus, description=CheckoutChargeStatus.__doc__),
)

CheckoutAuthorizeStatusEnum = doc(
    DOC_CATEGORY_CHECKOUT,
    to_enum(CheckoutAuthorizeStatus, description=CheckoutAuthorizeStatus.__doc__),
)

CheckoutCreateFromOrderErrorCode = doc(
    DOC_CATEGORY_CHECKOUT,
    graphene.Enum.from_enum(error_codes.CheckoutCreateFromOrderErrorCode),
)

CheckoutCreateFromOrderUnavailableVariantErrorCode = doc(
    DOC_CATEGORY_CHECKOUT,
    graphene.Enum.from_enum(
        error_codes.CheckoutCreateFromOrderUnavailableVariantErrorCode
    ),
)
