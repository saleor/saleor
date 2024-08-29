import pytest
from django.db.models import Q, Sum

from .. import WarehouseClickAndCollectOption
from ..models import Stock, Warehouse


def test_applicable_for_click_and_collect_finds_warehouse_with_all_and_local(
    stocks_for_cc, warehouses_for_cc, checkout_with_items_for_cc, channel_USD
):
    # given

    # all lines in local warehouse are available only in last CC
    local_warehouse_id = warehouses_for_cc[3].id

    # as there is a local warehouse from which the products can be shipped,
    # all warehouses with `ALL_WAREHOUSES` option should be returned as well
    expected_warehouses = Warehouse.objects.filter(
        Q(click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES)
        | Q(id=local_warehouse_id)
    )

    lines = checkout_with_items_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert set(result.values_list("id", flat=True)) == set(
        expected_warehouses.values_list("id", flat=True)
    )


def test_applicable_for_click_and_collect_warehouse_with_all_not_available_in_channel(
    stocks_for_cc, warehouses_for_cc, checkout_with_items_for_cc, channel_USD
):
    # given
    # all lines in local warehouse are available only in last CC
    local_warehouse_id = warehouses_for_cc[3].id

    # remove the channel from the warehouse with `ALL_WAREHOUSES` option
    all_warehouse = warehouses_for_cc[1]
    all_warehouse.channels.remove(channel_USD)

    lines = checkout_with_items_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert len(result) == 1
    assert result.first().id == local_warehouse_id


def test_applicable_for_click_and_collect_quantity_exceeded(
    stocks_for_cc, checkout_with_items_for_cc, channel_USD
):
    # given
    lines = checkout_with_items_for_cc.lines.all()
    line = lines[2]
    # line quantity is above the available stock in all warehouses
    quantity_above_available_in_stock = (
        Stock.objects.filter(product_variant=line.variant)
        .aggregate(total_quantity=Sum("quantity"))
        .get("total_quantity")
        + 1
    )

    line.quantity = quantity_above_available_in_stock
    line.save(update_fields=["quantity"])
    checkout_with_items_for_cc.refresh_from_db()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert result.count() == 0


def test_applicable_for_click_and_collect_quantity_exceeded_for_local(
    stocks_for_cc, checkout_with_items_for_cc, channel_USD
):
    # given
    expected_number_of_warehouses = Warehouse.objects.filter(
        click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES
    ).count()

    lines = checkout_with_items_for_cc.lines.all()
    line = lines[2]
    # line quantity is above the available stock in local warehouse
    quantity_above_local_available_in_stock = (
        Stock.objects.filter(product_variant=line.variant)
        .order_by("-quantity")
        .first()
        .quantity
        + 1
    )

    line.quantity = quantity_above_local_available_in_stock
    line.save(update_fields=["quantity"])

    # ensure that the line quantity can be collected from different warehouses
    assert (
        Stock.objects.filter(product_variant=line.variant)
        .aggregate(total_quantity=Sum("quantity"))
        .get("total_quantity")
    ) > quantity_above_local_available_in_stock

    checkout_with_items_for_cc.refresh_from_db()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert result.count() == expected_number_of_warehouses
    with pytest.raises(Warehouse.DoesNotExist):
        result.get(click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK)


def test_applicable_for_click_and_collect_for_one_line_two_local_warehouses(
    stocks_for_cc, checkout_with_item_for_cc, channel_USD
):
    # given

    # line is available in two local warehouses,
    # so also in warehouse with `ALL_WAREHOUSES` option, as the product can be shipped
    # from one of the locals
    warehouse_ids = set(
        Stock.objects.filter(
            Q(product_variant=checkout_with_item_for_cc.lines.first().variant)
            & Q(
                warehouse__click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
            )
            | Q(
                warehouse__click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES
            )
        ).values_list("warehouse_id", flat=True)
    )

    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert result.count() == len(warehouse_ids)
    assert set(result.values_list("id", flat=True)) == warehouse_ids


def test_applicable_for_click_and_collect_does_not_show_warehouses_with_empty_stocks(
    stocks_for_cc, checkout_with_items_for_cc, channel_USD
):
    # given
    line_with_empty_stock = checkout_with_items_for_cc.lines.last()

    stocks = Stock.objects.filter(product_variant=line_with_empty_stock.variant)
    empty_stock = stocks.filter(
        warehouse__click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK
    ).first()
    empty_stock.quantity = 0
    empty_stock.save(update_fields=["quantity"])

    warehouse_ids = set(
        stocks.exclude(id=empty_stock.id).values_list("warehouse_id", flat=True)
    )

    lines = checkout_with_items_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert result.count() == len(warehouse_ids)
    assert set(result.values_list("id", flat=True)) == warehouse_ids


def test_applicable_for_click_and_collect_additional_stock_does_not_change_availbility(
    stocks_for_cc,
    checkout_with_items_for_cc,
    warehouses_for_cc,
    product_variant_list,
    channel_USD,
):
    # given
    expected_total_number_of_stocks = 5
    expected_total_number_of_warehouses = 2
    expected_number_of_checkout_lines = 3

    Stock.objects.create(
        warehouse=warehouses_for_cc[3], product_variant=product_variant_list[3]
    )
    lines = checkout_with_items_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
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
    # given
    lines = checkout_with_items_for_cc.lines.all()
    warehouse_for_cc.shipping_zones.filter(name="Poland").delete()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_PLN.id)

    # then
    assert not result
