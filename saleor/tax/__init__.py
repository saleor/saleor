class TaxCalculationStrategy:
    FLAT_RATES = "FLAT_RATES"
    TAX_APP = "TAX_APP"

    CHOICES = [(FLAT_RATES, "Flat rates"), (TAX_APP, "Tax app")]


class TaxableObjectDiscountType:
    SUBTOTAL = "SUBTOTAL"
    SHIPPING = "SHIPPING"

    CHOICES = [(SUBTOTAL, "Subtotal"), (SHIPPING, "Shipping")]
