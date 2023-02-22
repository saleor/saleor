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


class MarkAsPaidStrategy:
    """Determine the mark as paid strategy for the channel.

    TRANSACTION_FLOW - new orders marked as paid will receive a
    `TransactionItem` object, that will cover the `order.total`.

    PAYMENT_FLOW - new orders marked as paid will receive a
    `Payment` object, that will cover the `order.total`.

    """

    TRANSACTION_FLOW = "transaction_flow"
    PAYMENT_FLOW = "payment_flow"

    CHOICES = [
        (TRANSACTION_FLOW, "Use transaction"),
        (PAYMENT_FLOW, "Use payment"),
    ]


class TransactionFlowStrategy:
    """Determine the transaction flow strategy.

    AUTHORIZATION - the processed transaction should be only authorized
    CHARGE - the processed transaction should be charged.
    """

    AUTHORIZATION = "authorization"
    CHARGE = "charge"

    CHOICES = [(AUTHORIZATION, "Authorize"), (CHARGE, "Charge")]
