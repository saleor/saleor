from ...channel import AllocationStrategy, MarkAsPaidStrategy, TransactionFlowStrategy
from ..core.doc_category import (
    DOC_CATEGORY_CHANNELS,
    DOC_CATEGORY_PAYMENTS,
    DOC_CATEGORY_PRODUCTS,
)
from ..core.enums import to_enum
from ..directives import doc

AllocationStrategyEnum = doc(
    DOC_CATEGORY_PRODUCTS,
    to_enum(
        AllocationStrategy,
        type_name="AllocationStrategyEnum",
        description=AllocationStrategy.__doc__,
    ),
)

MarkAsPaidStrategyEnum = doc(
    DOC_CATEGORY_CHANNELS,
    to_enum(
        MarkAsPaidStrategy,
        type_name="MarkAsPaidStrategyEnum",
        description=MarkAsPaidStrategy.__doc__,
    ),
)

TransactionFlowStrategyEnum = doc(
    DOC_CATEGORY_PAYMENTS,
    field=to_enum(
        TransactionFlowStrategy,
        type_name="TransactionFlowStrategyEnum",
        description=TransactionFlowStrategy.__doc__,
    ),
)
