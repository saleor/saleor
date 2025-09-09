from ...tax import TaxableObjectDiscountType
from ...tax import TaxCalculationStrategy as InternalTaxCalculationStrategy
from ..core.doc_category import DOC_CATEGORY_TAXES
from ..core.enums import to_enum
from ..directives import doc


def description(enum):
    if enum == InternalTaxCalculationStrategy.FLAT_RATES:
        return "Use flat rates to calculate taxes."
    if enum == InternalTaxCalculationStrategy.TAX_APP:
        return "Use tax app or plugin to calculate taxes."
    return None


TaxCalculationStrategy = doc(
    DOC_CATEGORY_TAXES,
    to_enum(
        InternalTaxCalculationStrategy,
        description=description,
        type_name="TaxCalculationStrategy",
    ),
)

TaxableObjectDiscountTypeEnum = doc(
    DOC_CATEGORY_TAXES,
    field=to_enum(
        TaxableObjectDiscountType,
        description="Indicates which part of the order the discount should affect: SUBTOTAL or SHIPPING.",
    ),
)
