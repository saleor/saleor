class AllocationStrategy:
    """Determine the allocation strategy for the channel.

    PRIORITIZE_SORTING_ORDER - the allocation is prioritized by the warehouses' sort
    order within the channel

    PRIORITIZE_HIGH_STOCK - the allocation is prioritized by the highest available
    quantity in stocks
    """

    PRIORITIZE_SORTING_ORDER = "prioritize-sorting-order"
    PRIORITIZE_HIGH_STOCK = "prioritize-high-stock"

    CHOICES = [
        (PRIORITIZE_SORTING_ORDER, "Prioritize sorting order"),
        (PRIORITIZE_HIGH_STOCK, "Prioritize high stock"),
    ]
