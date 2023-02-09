from ...channel import AllocationStrategy, MarkAsPaidStrategy
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
