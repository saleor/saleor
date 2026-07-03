from django.db.models import Sum
from django.db.models.functions import Coalesce


def get_quantity_allocated_for_stock(stock):
    """Count how many items are allocated for stock."""
    return stock.allocations.aggregate(
        quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
    )["quantity_allocated"]


def get_available_quantity_for_stock(stock):
    """Count how many stock items are available."""
    quantity_allocated = get_quantity_allocated_for_stock(stock)
    return max(stock.quantity - quantity_allocated, 0)
