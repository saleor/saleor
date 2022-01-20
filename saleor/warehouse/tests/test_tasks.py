import pytest

from ..tasks import update_stocks_quantity_allocated_task


@pytest.mark.parametrize(
    "allocation_allocated, stock_allocated, expected",
    (
        (10, 9, 10),
        (9, 10, 9),
        (0, 9, 0),
        (9, 0, 9),
    ),
)
def test_update_stocks_quantity_allocated_task(
    allocation_allocated, stock_allocated, expected, allocation
):
    allocation.quantity_allocated = allocation_allocated
    allocation.save(update_fields=["quantity_allocated"])
    stock = allocation.stock
    stock.quantity_allocated = stock_allocated
    stock.save(update_fields=["quantity_allocated"])

    update_stocks_quantity_allocated_task()

    allocation.refresh_from_db()
    stock.refresh_from_db()
    assert allocation.quantity_allocated == allocation_allocated
    assert stock.quantity_allocated == allocation_allocated


def test_update_stocks_quantity_allocated_task_stock_without_allocations(stock):
    stock_allocated = 9

    stock.allocations.all().delete()
    stock.quantity_allocated = stock_allocated
    stock.save(update_fields=["quantity_allocated"])

    update_stocks_quantity_allocated_task()

    stock.refresh_from_db()
    assert stock.quantity_allocated == 0
