from typing import Final

import graphene

from ...checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus, error_codes
from ..core.doc_category import DOC_CATEGORY_CHECKOUT, DOC_CATEGORY_ORDERS
from ..core.enums import to_enum

OrderCreateFromCheckoutErrorCode: Final[graphene.Enum] = graphene.Enum.from_enum(
    error_codes.OrderCreateFromCheckoutErrorCode
)
OrderCreateFromCheckoutErrorCode.doc_category = DOC_CATEGORY_ORDERS

CheckoutChargeStatusEnum: Final[graphene.Enum] = to_enum(
    CheckoutChargeStatus, description=CheckoutChargeStatus.__doc__
)
CheckoutChargeStatusEnum.doc_category = DOC_CATEGORY_CHECKOUT

CheckoutAuthorizeStatusEnum: Final[graphene.Enum] = to_enum(
    CheckoutAuthorizeStatus, description=CheckoutAuthorizeStatus.__doc__
)
CheckoutAuthorizeStatusEnum.doc_category = DOC_CATEGORY_CHECKOUT

CheckoutCreateFromOrderErrorCode: Final[graphene.Enum] = graphene.Enum.from_enum(
    error_codes.CheckoutCreateFromOrderErrorCode
)
CheckoutCreateFromOrderErrorCode.doc_category = DOC_CATEGORY_CHECKOUT

CheckoutCreateFromOrderUnavailableVariantErrorCode: Final[graphene.Enum] = (
    graphene.Enum.from_enum(
        error_codes.CheckoutCreateFromOrderUnavailableVariantErrorCode
    )
)
CheckoutCreateFromOrderUnavailableVariantErrorCode.doc_category = DOC_CATEGORY_CHECKOUT
