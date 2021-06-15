import pytest

from saleor.warehouse import WarehouseClickAndCollectOption

from ..models import Warehouse


def test_applicable_for_click_and_collect_finds_warehouse_with_all_and_local(
    stocks_for_cc, checkout_for_cc
):
    lines = checkout_for_cc.lines.all()
    result = Warehouse.objects.applicable_for_click_and_collect(lines)
    result.get(click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES)
    warehouse2 = result.get(
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
    )

    assert result.count() == 2
    assert warehouse2.stock_set.count() == lines.count()


def test_applicable_for_click_and_collect_quantity_exceeded_for_local(
    stocks_for_cc, checkout_for_cc
):
    lines = checkout_for_cc.lines.all()
    line = lines[2]
    line.quantity = 20
    line.save(update_fields=["quantity"])
    checkout_for_cc.refresh_from_db()

    result = Warehouse.objects.applicable_for_click_and_collect(lines)
    assert result.count() == 1
    with pytest.raises(Warehouse.DoesNotExist):
        result.get(click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK)
