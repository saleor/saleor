from typing import Final

import graphene

from ...channel import AllocationStrategy, MarkAsPaidStrategy, TransactionFlowStrategy
from ..core.descriptions import DEPRECATED_LEGACY_PAYMENTS
from ..core.doc_category import (
    DOC_CATEGORY_CHANNELS,
    DOC_CATEGORY_PAYMENTS,
    DOC_CATEGORY_PRODUCTS,
)
from ..core.enums import to_enum

AllocationStrategyEnum: Final[graphene.Enum] = to_enum(
    AllocationStrategy,
    type_name="AllocationStrategyEnum",
    description=AllocationStrategy.__doc__,
)
AllocationStrategyEnum.doc_category = DOC_CATEGORY_PRODUCTS


def mark_as_paid_strategy_deprecation_reason(enum):
    if enum.value == MarkAsPaidStrategy.PAYMENT_FLOW:
        return DEPRECATED_LEGACY_PAYMENTS
    return None


MarkAsPaidStrategyEnum: Final[graphene.Enum] = to_enum(
    MarkAsPaidStrategy,
    type_name="MarkAsPaidStrategyEnum",
    description=MarkAsPaidStrategy.__doc__,
    deprecation_reason=mark_as_paid_strategy_deprecation_reason,
)
MarkAsPaidStrategyEnum.doc_category = DOC_CATEGORY_CHANNELS

TransactionFlowStrategyEnum: Final[graphene.Enum] = to_enum(
    TransactionFlowStrategy,
    type_name="TransactionFlowStrategyEnum",
    description=TransactionFlowStrategy.__doc__,
)
TransactionFlowStrategyEnum.doc_category = DOC_CATEGORY_PAYMENTS
