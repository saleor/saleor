from typing import Final

import graphene

from ...channel import AllocationStrategy, MarkAsPaidStrategy, TransactionFlowStrategy
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

MarkAsPaidStrategyEnum: Final[graphene.Enum] = to_enum(
    MarkAsPaidStrategy,
    type_name="MarkAsPaidStrategyEnum",
    description=MarkAsPaidStrategy.__doc__,
)
MarkAsPaidStrategyEnum.doc_category = DOC_CATEGORY_CHANNELS

TransactionFlowStrategyEnum: Final[graphene.Enum] = to_enum(
    TransactionFlowStrategy,
    type_name="TransactionFlowStrategyEnum",
    description=TransactionFlowStrategy.__doc__,
)
TransactionFlowStrategyEnum.doc_category = DOC_CATEGORY_PAYMENTS
