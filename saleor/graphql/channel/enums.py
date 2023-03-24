from ...channel import AllocationStrategy
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.enums import to_enum

AllocationStrategyEnum = to_enum(
    AllocationStrategy,
    type_name="AllocationStrategyEnum",
    description=AllocationStrategy.__doc__,
)
AllocationStrategyEnum.doc_category = DOC_CATEGORY_PRODUCTS
