from django.db.models import Sum
from django.db.models.functions import Coalesce

from saleor.warehouse.models import Stock, Warehouse


def get_quantity_allocated_for_stock(stock):
    """Count how many items are allocated for stock."""
    return stock.allocations.aggregate(
        quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
    )["quantity_allocated"]


def get_available_quantity_for_stock(stock):
    """Count how many stock items are available."""
    quantity_allocated = get_quantity_allocated_for_stock(stock)
    return max(stock.quantity - quantity_allocated, 0)


def compare_stocks_quantity_from_channel(
    first_channel, second_channel, first_quantity, second_quantity
):
    assert (
        _get_aggregate_stock_quantity_from_channel(first_channel.slug) == first_quantity
    )
    assert (
        _get_aggregate_stock_quantity_from_channel(second_channel.slug)
        == second_quantity
    )


def create_test_warehouse_with_stocks(
    allocation, warehouse_name, warehouse_slug, address, shipping_zones
):
    second_test_warehouse = Warehouse.objects.create(
        name=warehouse_name, slug=warehouse_slug, address=address.get_copy()
    )
    second_test_warehouse.shipping_zones.set(shipping_zones)
    Stock.objects.create(
        warehouse=second_test_warehouse,
        product_variant=allocation.order_line.variant,
        quantity=20,
    )
    return second_test_warehouse


def _get_aggregate_stock_quantity_from_channel(channel_slug):
    return Stock.objects.for_channel(channel_slug).aggregate(Sum("quantity"))[
        "quantity__sum"
    ]
