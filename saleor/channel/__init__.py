class AllocationStrategy:
    """Determine the allocation strategy for the channel.

    PRIORITIZE_SORTING_ORDER - allocate stocks according to the warehouses' order
    within the channel

    PRIORITIZE_HIGH_STOCK - allocate stock in a warehouse with the most stock
    """

    PRIORITIZE_SORTING_ORDER = "prioritize-sorting-order"
    PRIORITIZE_HIGH_STOCK = "prioritize-high-stock"

    CHOICES = [
        (PRIORITIZE_SORTING_ORDER, "Prioritize sorting order"),
        (PRIORITIZE_HIGH_STOCK, "Prioritize high stock"),
    ]
