import graphene

from ...checkout import error_codes
from ..core.doc_category import DOC_CATEGORY_ORDERS

OrderCreateFromCheckoutErrorCode = graphene.Enum.from_enum(
    error_codes.OrderCreateFromCheckoutErrorCode
)
OrderCreateFromCheckoutErrorCode.doc_category = DOC_CATEGORY_ORDERS
