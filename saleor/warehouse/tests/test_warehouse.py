import pytest
from django.db.models import Sum

from .. import WarehouseClickAndCollectOption
from ..models import Stock, Warehouse


def test_applicable_for_click_and_collect_finds_warehouse_with_all_and_local(
    stocks_for_cc, checkout_with_items_for_cc, channel_USD
):
    expected_number_of_warehouses = 2

    lines = checkout_with_items_for_cc.lines.all()
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)
    result.get(click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES)
    warehouse2 = result.get(
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
    )

    assert result.count() == expected_number_of_warehouses
    assert warehouse2.stock_set.count() == lines.count()


def test_applicable_for_click_and_collect_quantity_exceeded_for_local(
    stocks_for_cc, checkout_with_items_for_cc, channel_USD
):
    expected_number_of_warehouses = Warehouse.objects.filter(
        click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES
    ).count()

    lines = checkout_with_items_for_cc.lines.all()
    line = lines[2]
    quantity_above_available_in_stock = (
        Stock.objects.filter(product_variant=line.variant)
        .aggregate(total_quantity=Sum("quantity"))
        .get("total_quantity")
        + 1
    )

    line.quantity = quantity_above_available_in_stock
    line.save(update_fields=["quantity"])
    checkout_with_items_for_cc.refresh_from_db()

    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)
    assert result.count() == expected_number_of_warehouses
    with pytest.raises(Warehouse.DoesNotExist):
        result.get(click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK)


def test_applicable_for_click_and_collect_for_one_line_two_local_warehouses(
    stocks_for_cc, checkout_with_item_for_cc, channel_USD
):
    expected_total_number_of_warehouses = Warehouse.objects.exclude(
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED
    ).count()
    expected_total_number_of_local_warehouses = Warehouse.objects.filter(
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
    ).count()
    expected_total_number_of_all_warehouses = (
        expected_total_number_of_warehouses - expected_total_number_of_local_warehouses
    )

    lines = checkout_with_item_for_cc.lines.all()
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)
    assert result.count() == expected_total_number_of_warehouses
    assert (
        result.filter(
            click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
        ).count()
        == expected_total_number_of_local_warehouses
    )
    assert (
        result.filter(
            click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES
        ).count()
        == expected_total_number_of_all_warehouses
    )


def test_applicable_for_click_and_collect_does_not_show_warehouses_with_empty_stocks(
    stocks_for_cc, checkout_with_items_for_cc, channel_USD
):
    expected_total_number_of_warehouses = 1
    reduced_stock_quantity = 0

    lines = checkout_with_items_for_cc.lines.all()
    stock = Stock.objects.filter(
        warehouse__click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
    ).last()
    stock.quantity = reduced_stock_quantity
    stock.save(update_fields=["quantity"])

    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)
    assert result.count() == expected_total_number_of_warehouses
    assert (
        result.first().click_and_collect_option
        == WarehouseClickAndCollectOption.ALL_WAREHOUSES
    )


def test_applicable_for_click_and_collect_additional_stock_does_not_change_availbility(
    stocks_for_cc,
    checkout_with_items_for_cc,
    warehouses_for_cc,
    product_variant_list,
    channel_USD,
):
    expected_total_number_of_stocks = 5
    expected_total_number_of_warehouses = 2
    expected_number_of_checkout_lines = 3

    Stock.objects.create(
        warehouse=warehouses_for_cc[3], product_variant=product_variant_list[3]
    )
    lines = checkout_with_items_for_cc.lines.all()

    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    assert result.count() == expected_total_number_of_warehouses
    result.get(click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES)
    warehouse = result.get(
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
    )
    assert warehouse == warehouses_for_cc[3]
    # Taken from warehouses fixture, due to the prefetch_related on stocks qs for lines
    assert warehouses_for_cc[3].stock_set.count() == expected_total_number_of_stocks
    assert lines.count() == expected_number_of_checkout_lines


def test_applicable_for_click_and_collect_returns_empty_collection_if_no_channels(
    warehouse_for_cc, checkout_with_items_for_cc, channel_USD
):
    lines = checkout_with_items_for_cc.lines.all()
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)
    assert result.count() == 1

    warehouse_for_cc.channels.clear()
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    assert not result


def test_applicable_for_click_and_collect_returns_empty_collection_if_different_channel(
    warehouse_for_cc, checkout_with_items_for_cc, channel_PLN
):
    lines = checkout_with_items_for_cc.lines.all()
    warehouse_for_cc.shipping_zones.filter(name="Poland").delete()

    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_PLN.id)

    assert not result
