from ...tax import TaxCalculationStrategy as InternalTaxCalculationStrategy
from ..core.doc_category import DOC_CATEGORY_TAXES
from ..core.enums import to_enum


def description(enum):
    if enum == InternalTaxCalculationStrategy.FLAT_RATES:
        return "Use flat rates to calculate taxes."
    if enum == InternalTaxCalculationStrategy.TAX_APP:
        return "Use tax app or plugin to calculate taxes."
    return None


TaxCalculationStrategy = to_enum(
    InternalTaxCalculationStrategy,
    description=description,
    type_name="TaxCalculationStrategy",
)
TaxCalculationStrategy.doc_category = DOC_CATEGORY_TAXES
