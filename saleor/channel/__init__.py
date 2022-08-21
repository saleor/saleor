class AllocationStrategy:
    PRIORITIZE_SORTING_ORDER = "prioritize-sorting-order"
    PRIORITIZE_HIGH_STOCK = "prioritize-high-stock"

    CHOICES = [
        (PRIORITIZE_SORTING_ORDER, "Prioritize sorting order"),
        (PRIORITIZE_HIGH_STOCK, "Prioritize high stock"),
    ]
