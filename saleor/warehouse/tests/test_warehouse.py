import pytest
from django.db.models import Q, Sum

from ...order.models import OrderLine
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


def test_applicable_for_click_and_collect_stock_only_in_local_all_and_local_returned(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Esnure the `ALL` warehouse is returned when the stock is availble in local one.

    When the stock is available only in local warehouse, but not
    available in the warehouse with `ALL_WAREHOUSES` option, both warehouses
    are returned.
    """
    # given
    line = checkout_with_item_for_cc.lines.first()

    all_warehouse = warehouses_for_cc[1]
    local_warehouse = warehouses_for_cc[2]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line.variant, quantity=0),
            Stock(warehouse=local_warehouse, product_variant=line.variant, quantity=10),
        ]
    )

    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert len(result) == 2
    assert set(result.values_list("id", flat=True)) == {
        all_warehouse.id,
        local_warehouse.id,
    }


def test_applicable_for_click_and_collect_stock_only_in_warehouse_with_all_option(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Ensure that only `ALL` warehouse is returned when stock is available only there.

    When the stock is available only in warehouse with `ALL_WAREHOUSES`
    click and collect option, only this one is returned.
    """
    # given
    line = checkout_with_item_for_cc.lines.first()

    all_warehouse = warehouses_for_cc[1]
    local_warehouse = warehouses_for_cc[2]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line.variant, quantity=10),
            Stock(warehouse=local_warehouse, product_variant=line.variant, quantity=0),
        ]
    )

    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert len(result) == 1
    assert result.first().id == all_warehouse.id


def test_applicable_for_click_and_collect_all_returned_stock_collected_from_local(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Ensure that stocks can be collected from local warehouse to `ALL` warehouse.

    When the stock is not available in warehouse with `ALL_WAREHOUSES`
    click and collect option, but can be collected from the different warehouses,
    the warehouse with `ALL_WAREHOUSES` click and collect option is returned.
    """
    # given
    line = checkout_with_item_for_cc.lines.first()
    line.quantity = 5
    line.save(update_fields=["quantity"])

    all_warehouse = warehouses_for_cc[1]
    local_warehouse_1 = warehouses_for_cc[2]
    local_warehouse_2 = warehouses_for_cc[3]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line.variant, quantity=0),
            Stock(
                warehouse=local_warehouse_1, product_variant=line.variant, quantity=2
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line.variant, quantity=4
            ),
        ]
    )

    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert len(result) == 1
    assert result.first().id == all_warehouse.id


def test_applicable_for_click_and_collect_stock_from_local_but_not_all_in_channel(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Ensure the warehouse isn't returned when it's not available in the given channel.

    When the stock is not available in warehouse with `ALL_WAREHOUSES`
    click and collect option, but can be collected from the different warehouses,
    and the all warehouse is not available in given channel, the warehouse
    is not returned.
    """
    # given
    line = checkout_with_item_for_cc.lines.first()
    line.quantity = 5
    line.save(update_fields=["quantity"])

    all_warehouse = warehouses_for_cc[1]
    local_warehouse_1 = warehouses_for_cc[2]
    local_warehouse_2 = warehouses_for_cc[3]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line.variant, quantity=0),
            Stock(
                warehouse=local_warehouse_1, product_variant=line.variant, quantity=2
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line.variant, quantity=4
            ),
        ]
    )

    all_warehouse.channels.remove(channel_USD)
    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert len(result) == 0


def test_applicable_for_click_and_collect_all_returned_stock_from_disabled_warehouse(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Ensure that stocks can be collected from disabled warehouse to `ALL` warehouse.

    When the stock is not available in warehouse with `ALL_WAREHOUSES`
    click and collect option, but can be collected from the different warehouse
    with `DISABLED` click and collect option, the warehouse with `ALL_WAREHOUSES`
    option is returned.
    """
    # given
    line = checkout_with_item_for_cc.lines.first()

    all_warehouse = warehouses_for_cc[1]
    disabled_warehouse = warehouses_for_cc[0]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line.variant, quantity=0),
            Stock(
                warehouse=disabled_warehouse, product_variant=line.variant, quantity=10
            ),
        ]
    )

    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert len(result) == 1
    assert result.first().id == all_warehouse.id


def test_applicable_for_click_and_collect_stock_collected_from_different_warehouses(
    warehouses_for_cc, checkout_with_items_for_cc, channel_USD
):
    """Ensure that stock can be collected from mutliple different warehouses.

    When the all stock is not available in warehouse with
    `ALL_WAREHOUSES` click and collect option, but can be collected from the
    different warehouses, the warehouse with `ALL_WAREHOUSES` click and collect
    option is returned, only when the stock for all products can be collected.
    """
    # given
    line_1, line_2, line_3 = checkout_with_items_for_cc.lines.all()
    line_1.quantity = 5
    line_2.quantity = 3
    line_3.quantity = 7
    OrderLine.objects.bulk_update([line_1, line_2, line_3], ["quantity"])

    all_warehouse = warehouses_for_cc[1]
    local_warehouse_1 = warehouses_for_cc[2]
    local_warehouse_2 = warehouses_for_cc[3]
    disabled_warehouse = warehouses_for_cc[0]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line_1.variant, quantity=0),
            Stock(warehouse=all_warehouse, product_variant=line_2.variant, quantity=3),
            Stock(warehouse=all_warehouse, product_variant=line_3.variant, quantity=0),
            Stock(
                warehouse=local_warehouse_1, product_variant=line_1.variant, quantity=3
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line_1.variant, quantity=4
            ),
            Stock(
                warehouse=disabled_warehouse, product_variant=line_3.variant, quantity=5
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line_3.variant, quantity=3
            ),
        ]
    )

    lines = checkout_with_items_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert len(result) == 1
    assert result.first().id == all_warehouse.id


def test_applicable_for_click_and_collect_empty_result_when_not_all_products_available(
    warehouses_for_cc, checkout_with_items_for_cc, channel_USD
):
    """Ensure that stocks for all lines must be covered to return the warehouse.

    When there is no enough stock for at least one product, no warehouse
    is returned.
    """
    # given
    line_1, line_2, line_3 = checkout_with_items_for_cc.lines.all()
    line_1.quantity = 5
    line_2.quantity = 3
    line_3.quantity = 7
    OrderLine.objects.bulk_update([line_1, line_2, line_3], ["quantity"])

    all_warehouse = warehouses_for_cc[1]
    local_warehouse_1 = warehouses_for_cc[2]
    local_warehouse_2 = warehouses_for_cc[3]
    disabled_warehouse = warehouses_for_cc[0]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line_1.variant, quantity=0),
            Stock(warehouse=all_warehouse, product_variant=line_2.variant, quantity=0),
            Stock(warehouse=all_warehouse, product_variant=line_3.variant, quantity=0),
            Stock(
                warehouse=local_warehouse_1, product_variant=line_1.variant, quantity=3
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line_1.variant, quantity=4
            ),
            Stock(
                warehouse=disabled_warehouse, product_variant=line_3.variant, quantity=5
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line_3.variant, quantity=3
            ),
        ]
    )

    lines = checkout_with_items_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert len(result) == 0


def test_applicable_for_click_and_collect_additional_stocks(
    warehouses_for_cc, checkout_with_items_for_cc, channel_USD, variant
):
    """Ensure that stock of another variant will be not taken into account.

    When the warehouse has additional stock for another variant, and the warehouse stock
    number is equal to the number of variants, the warehouse is not returned.
    """
    # given
    line_1, line_2, line_3 = checkout_with_items_for_cc.lines.all()
    line_1.quantity = 5
    line_2.quantity = 3
    line_3.quantity = 7
    OrderLine.objects.bulk_update([line_1, line_2, line_3], ["quantity"])

    all_warehouse = warehouses_for_cc[1]
    local_warehouse_1 = warehouses_for_cc[2]
    local_warehouse_2 = warehouses_for_cc[3]
    disabled_warehouse = warehouses_for_cc[0]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line_1.variant, quantity=0),
            Stock(warehouse=all_warehouse, product_variant=line_2.variant, quantity=3),
            Stock(warehouse=all_warehouse, product_variant=line_3.variant, quantity=0),
            Stock(
                warehouse=local_warehouse_1, product_variant=line_1.variant, quantity=3
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line_1.variant, quantity=4
            ),
            Stock(
                warehouse=disabled_warehouse, product_variant=line_3.variant, quantity=5
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line_3.variant, quantity=3
            ),
            # stocks for different variant, causes that the number of stocks for
            # local_warehouse_2 is equal to the number of variants;
            # should not be taken into consideration, and local_warehouse_2 should
            # not be returned
            Stock(warehouse=local_warehouse_2, product_variant=variant, quantity=3),
        ]
    )

    lines = checkout_with_items_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect(lines, channel_USD.id)

    # then
    assert len(result) == 1
    assert result.first().id == all_warehouse.id


def test_applicable_for_click_and_collect_no_quantity_check_stock_available(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Ensure that when the stock exists in the warehouse, the warehouse is returned."""
    # given
    line = checkout_with_item_for_cc.lines.first()
    line.quantity = 10
    line.save(update_fields=["quantity"])

    all_warehouse = warehouses_for_cc[1]
    local_warehouse = warehouses_for_cc[2]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line.variant, quantity=0),
            Stock(warehouse=local_warehouse, product_variant=line.variant, quantity=1),
        ]
    )

    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect_no_quantity_check(
        lines, channel_USD.id
    )

    # then
    assert len(result) == 2
    assert set(result.values_list("id", flat=True)) == {
        all_warehouse.id,
        local_warehouse.id,
    }


def test_applicable_for_click_and_collect_no_quantity_check_stock_available_in_local(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Ensure that the stock for `ALL` warehouse can be collected from local one.

    When the stock is available in the local warehouse, also
    the warehouse with `ALL_WAREHOUSES` option is returned.
    """
    # given
    line = checkout_with_item_for_cc.lines.first()
    line.quantity = 10
    line.save(update_fields=["quantity"])

    all_warehouse = warehouses_for_cc[1]
    local_warehouse = warehouses_for_cc[2]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=local_warehouse, product_variant=line.variant, quantity=1),
        ]
    )

    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect_no_quantity_check(
        lines, channel_USD.id
    )

    # then
    assert len(result) == 2
    assert set(result.values_list("id", flat=True)) == {
        all_warehouse.id,
        local_warehouse.id,
    }


def test_applicable_for_click_and_collect_no_quantity_check_stock_available_in_disabled(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Ensure that the stock for `ALL` warehouse can be collected from disabled one.

    When the stock is available in the warehouse with `DISABLED`
    click and collect option, also the warehouse with `ALL_WAREHOUSES`
    option is returned.
    """
    # given
    line = checkout_with_item_for_cc.lines.first()
    line.quantity = 10
    line.save(update_fields=["quantity"])

    all_warehouse = warehouses_for_cc[1]
    disabled_warehouse = warehouses_for_cc[0]

    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=disabled_warehouse, product_variant=line.variant, quantity=1
            ),
        ]
    )

    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect_no_quantity_check(
        lines, channel_USD.id
    )

    # then
    assert len(result) == 1
    assert result.first().id == all_warehouse.id


def test_applicable_for_click_and_collect_no_quantity_check_no_stocks(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Ensure that when there are no stocks, no warehouse is returned."""
    # given
    line = checkout_with_item_for_cc.lines.first()
    line.quantity = 10
    line.save(update_fields=["quantity"])

    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect_no_quantity_check(
        lines, channel_USD.id
    )

    # then
    assert len(result) == 0


def test_applicable_for_click_and_collect_no_quantity_check_one_line_without_stock(
    warehouses_for_cc, checkout_with_items_for_cc, channel_USD
):
    """Ensure that when there are no stocks for all lines, no warehouse is returned."""
    # given
    line_1, line_2, line_3 = checkout_with_items_for_cc.lines.all()

    all_warehouse = warehouses_for_cc[1]
    local_warehouse = warehouses_for_cc[2]

    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=local_warehouse,
                product_variant=line_1.variant,
                quantity=0,
            ),
            Stock(warehouse=all_warehouse, product_variant=line_2.variant, quantity=0),
        ]
    )
    lines = checkout_with_items_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect_no_quantity_check(
        lines, channel_USD.id
    )

    # then
    assert len(result) == 0


def test_applicable_for_click_and_collect_no_quantity_check_no_channels(
    warehouses_for_cc, checkout_with_item_for_cc, channel_USD
):
    """Ensure the warehouse isn't returned when it's not available in the given channel."""
    # given
    line = checkout_with_item_for_cc.lines.first()
    line.quantity = 10
    line.save(update_fields=["quantity"])

    all_warehouse = warehouses_for_cc[1]
    local_warehouse = warehouses_for_cc[2]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=local_warehouse, product_variant=line.variant, quantity=1),
        ]
    )

    all_warehouse.channels.remove(channel_USD)
    lines = checkout_with_item_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect_no_quantity_check(
        lines, channel_USD.id
    )

    # then
    assert len(result) == 1
    assert result.first().id == local_warehouse.id


def test_applicable_for_click_and_collect_no_quantity_check_additional_stock(
    warehouses_for_cc, checkout_with_items_for_cc, channel_USD, variant
):
    """Ensure that stock of another variant will be not taken into account.

    When the warehouse has additional stock for another variant, and the warehouse stock
    number is equal to the number of variants, the warehouse is not returned.
    """
    # given
    line_1, line_2, line_3 = checkout_with_items_for_cc.lines.all()

    all_warehouse = warehouses_for_cc[1]
    local_warehouse_1 = warehouses_for_cc[2]
    local_warehouse_2 = warehouses_for_cc[3]

    Stock.objects.bulk_create(
        [
            Stock(warehouse=all_warehouse, product_variant=line_1.variant, quantity=1),
            Stock(
                warehouse=local_warehouse_1, product_variant=line_1.variant, quantity=1
            ),
            Stock(
                warehouse=local_warehouse_1, product_variant=line_2.variant, quantity=1
            ),
            Stock(
                warehouse=local_warehouse_2, product_variant=line_3.variant, quantity=1
            ),
            # stock for different variant, causes that the number of stocks for
            # local_warehouse_1 is equal to the number of variants;
            # should not be taken into consideration, and local_warehouse_2 should
            # not be returned
            Stock(warehouse=local_warehouse_1, product_variant=variant, quantity=1),
        ]
    )

    lines = checkout_with_items_for_cc.lines.all()

    # when
    result = Warehouse.objects.applicable_for_click_and_collect_no_quantity_check(
        lines, channel_USD.id
    )

    # then
    assert len(result) == 1
    assert result.first().id == all_warehouse.id


def test_for_channel_with_active_shipping_zone_or_cc(
    warehouses_for_cc, warehouse, warehouse_JPY, warehouse_no_shipping_zone, channel_USD
):
    # given
    expected_warehouse_pks = [wh.pk for wh in warehouses_for_cc]
    expected_warehouse_pks.append(warehouse.pk)

    # when
    warehouses = Warehouse.objects.for_channel_with_active_shipping_zone_or_cc(
        channel_USD.slug
    )

    # then
    assert set(warehouses.values_list("pk", flat=True)) == set(expected_warehouse_pks)
