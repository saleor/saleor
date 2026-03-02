from typing import Final

import graphene

from ...graphql.core.enums import to_enum
from ...inventory import (
    PurchaseOrderItemAdjustmentReason,
    PurchaseOrderItemStatus,
    PurchaseOrderStatus,
)
from ..core.doc_category import DOC_CATEGORY_PRODUCTS

PurchaseOrderItemStatusEnum: Final[graphene.Enum] = to_enum(
    PurchaseOrderItemStatus, type_name="PurchaseOrderItemStatusEnum"
)
PurchaseOrderItemStatusEnum.doc_category = DOC_CATEGORY_PRODUCTS

PurchaseOrderItemAdjustmentReasonEnum: Final[graphene.Enum] = to_enum(
    PurchaseOrderItemAdjustmentReason, type_name="PurchaseOrderItemAdjustmentReasonEnum"
)
PurchaseOrderItemAdjustmentReasonEnum.doc_category = DOC_CATEGORY_PRODUCTS

PurchaseOrderStatusEnum: Final[graphene.Enum] = to_enum(
    PurchaseOrderStatus, type_name="PurchaseOrderStatusEnum"
)
PurchaseOrderStatusEnum.doc_category = DOC_CATEGORY_PRODUCTS


class PurchaseOrderItemAdjustmentStatusEnum(graphene.Enum):
    PENDING = "pending"
    PROCESSED = "processed"

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
