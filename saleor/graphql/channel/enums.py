from ...channel import AllocationStrategy, MarkAsPaidStrategy, TransactionFlowStrategy
from ..core.enums import to_enum

AllocationStrategyEnum = to_enum(
    AllocationStrategy,
    type_name="AllocationStrategyEnum",
    description=AllocationStrategy.__doc__,
)

MarkAsPaidStrategyEnum = to_enum(
    MarkAsPaidStrategy,
    type_name="MarkAsPaidStrategyEnum",
    description=MarkAsPaidStrategy.__doc__,
)

TransactionFlowStrategyEnum = to_enum(
    TransactionFlowStrategy,
    type_name="TransactionFlowStrategyEnum",
    description=TransactionFlowStrategy.__doc__,
)
