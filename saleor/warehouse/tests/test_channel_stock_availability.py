from .. import WarehouseClickAndCollectOption
from ..channel_stock_availability import (
    trigger_back_in_stock_in_channel_events_for_stocks,
    trigger_out_of_stock_in_channel_events_for_stocks,
)
from ..interface import VariantChannelStockInfo
from ..models import Allocation, Stock, Warehouse

OUT_IN_CHANNEL = (
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_out_of_stock_in_channel"
)
BACK_IN_CHANNEL = (
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_back_in_stock_in_channel"
)
OUT_CC = (
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_out_of_stock_for_click_and_collect"
)
BACK_CC = (
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_back_in_stock_for_click_and_collect"
)


def test_out_of_stock_fires_when_only_warehouse_in_bucket(
    variant, warehouse, channel_USD, site_settings, mocker
):
    # given - single non-C&C warehouse in the channel, stock just hit 0
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    mocked_out_cc = mocker.patch(OUT_CC)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=0
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then
    info = mocked_out.call_args.args[0]
    assert info == VariantChannelStockInfo(
        variant_id=variant.id, channel_slug=channel_USD.slug
    )
    mocked_out_cc.assert_not_called()


def test_out_of_stock_does_not_fire_when_another_warehouse_has_stock(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - second non-C&C warehouse in same channel still has availability
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=0
    )
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    Stock.objects.create(product_variant=variant, warehouse=other_warehouse, quantity=5)

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then
    mocked_out.assert_not_called()


def test_out_of_stock_fires_even_when_cc_warehouse_in_channel_has_stock(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - non-C&C stock at 0; C&C warehouse with stock must not block event
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    mocked_out_cc = mocker.patch(OUT_CC)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=0
    )
    cc_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="cc",
        slug="cc",
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
    )
    cc_warehouse.channels.add(channel_USD)
    Stock.objects.create(product_variant=variant, warehouse=cc_warehouse, quantity=5)

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then - non-C&C bucket is empty, event fires; C&C event is not raised
    mocked_out.assert_called_once()
    mocked_out_cc.assert_not_called()


def test_out_of_stock_in_cc_warehouse_fires_click_and_collect_event(
    variant, channel_USD, address, site_settings, mocker
):
    # given - C&C-only warehouse, stock just hit 0
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    mocked_out_cc = mocker.patch(OUT_CC)
    cc_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="cc-only",
        slug="cc-only",
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
    )
    cc_warehouse.channels.add(channel_USD)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=cc_warehouse, quantity=0
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then
    info = mocked_out_cc.call_args.args[0]
    assert info.channel_slug == channel_USD.slug
    mocked_out.assert_not_called()


def test_back_in_stock_fires_when_all_other_warehouses_in_bucket_are_empty(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - other non-C&C warehouse exists but has zero available
    mocked_back = mocker.patch(BACK_IN_CHANNEL)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=10
    )
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    Stock.objects.create(product_variant=variant, warehouse=other_warehouse, quantity=0)

    # when
    trigger_back_in_stock_in_channel_events_for_stocks([stock], site_settings)

    # then
    mocked_back.assert_called_once()


def test_back_in_stock_does_not_fire_when_another_warehouse_already_has_stock(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - another warehouse already has stock, so this isn't the "first back"
    mocked_back = mocker.patch(BACK_IN_CHANNEL)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=10
    )
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    Stock.objects.create(product_variant=variant, warehouse=other_warehouse, quantity=4)

    # when
    trigger_back_in_stock_in_channel_events_for_stocks([stock], site_settings)

    # then
    mocked_back.assert_not_called()


def test_does_not_fire_when_warehouse_belongs_to_no_channels(
    variant, address, site_settings, mocker
):
    # given - warehouse not attached to any channel
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    orphan = Warehouse.objects.create(
        address=address.get_copy(),
        name="orphan",
        slug="orphan",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    stock = Stock.objects.create(product_variant=variant, warehouse=orphan, quantity=0)

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then
    mocked_out.assert_not_called()


def test_fires_only_for_channels_whose_bucket_is_empty(
    variant, warehouse, channel_USD, channel_PLN, address, site_settings, mocker
):
    # given - warehouse belongs to two channels; only one has another warehouse
    # with remaining stock
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    warehouse.channels.add(channel_PLN)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=0
    )
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other-usd",
        slug="other-usd",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    Stock.objects.create(product_variant=variant, warehouse=other_warehouse, quantity=5)

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then - PLN bucket is empty (only `warehouse`), USD has another with stock
    mocked_out.assert_called_once()
    info = mocked_out.call_args.args[0]
    assert info.channel_slug == channel_PLN.slug


def test_out_of_stock_fires_when_other_warehouse_has_only_fully_allocated_stock(
    variant, warehouse, channel_USD, address, site_settings, order_line, mocker
):
    # given - other warehouse has quantity but everything is allocated
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=0
    )
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    other_stock = Stock.objects.create(
        product_variant=variant, warehouse=other_warehouse, quantity=5
    )
    Allocation.objects.create(
        order_line=order_line, stock=other_stock, quantity_allocated=5
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then - other stock has 0 available -> event fires
    mocked_out.assert_called_once()


def test_out_of_stock_ignores_stocks_of_other_variants_in_same_bucket(
    variant,
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - other warehouse has stock for a *different* variant
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=0
    )
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    other_variant = product_with_two_variants.variants.first()
    Stock.objects.create(
        product_variant=other_variant, warehouse=other_warehouse, quantity=10
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then - other variant's stock is irrelevant; bucket is empty for tested variant
    mocked_out.assert_called_once()


def test_out_of_stock_ignores_warehouse_stock_attached_to_different_channel(
    variant, warehouse, channel_USD, channel_PLN, address, site_settings, mocker
):
    # given - other warehouse with stock exists, but only in a different channel
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=0
    )
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="pln-only",
        slug="pln-only",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_PLN)
    Stock.objects.create(product_variant=variant, warehouse=other_warehouse, quantity=5)

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then - the USD bucket has no other warehouses, event fires
    mocked_out.assert_called_once()
    info = mocked_out.call_args.args[0]
    assert info.channel_slug == channel_USD.slug


def test_trigger_forwards_site_settings_requestor_and_webhooks(
    variant, warehouse, channel_USD, site_settings, mocker
):
    # given
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=0
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then
    args, kwargs = mocked_out.call_args
    assert args[1] is site_settings
    assert kwargs["requestor"] is None
    assert kwargs["webhooks"] is None


# --- Multi-stock (bulk) tests ---


def test_bulk_fires_for_multiple_stocks_in_same_warehouse(
    product_with_two_variants, warehouse, channel_USD, site_settings, mocker
):
    # given - two variants in the same warehouse, both at 0
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    for stock in stocks:
        stock.quantity = 0
    Stock.objects.bulk_update(stocks, ["quantity"])

    # when
    trigger_out_of_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then - one event per (stock, channel) pair
    assert mocked_out.call_count == 2
    fired_variant_ids = {call.args[0].variant_id for call in mocked_out.call_args_list}
    assert fired_variant_ids == {variants[0].id, variants[1].id}


def test_bulk_does_not_fire_when_other_warehouse_covers_all_variants(
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - another non-C&C warehouse in the same channel has stock for both
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    for stock in stocks:
        stock.quantity = 0
    Stock.objects.bulk_update(stocks, ["quantity"])
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    Stock.objects.bulk_create(
        [
            Stock(product_variant=variants[0], warehouse=other_warehouse, quantity=5),
            Stock(product_variant=variants[1], warehouse=other_warehouse, quantity=3),
        ]
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then - neither fires, the other warehouse covers both variants
    mocked_out.assert_not_called()


def test_bulk_fires_selectively_when_other_warehouse_covers_only_one_variant(
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - another warehouse has stock only for variants[0], not variants[1]
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    for stock in stocks:
        stock.quantity = 0
    Stock.objects.bulk_update(stocks, ["quantity"])
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    Stock.objects.create(
        product_variant=variants[0], warehouse=other_warehouse, quantity=5
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then - only variants[1] fires (variants[0] is covered by other_warehouse)
    mocked_out.assert_called_once()
    assert mocked_out.call_args.args[0].variant_id == variants[1].id


def test_bulk_stocks_from_different_warehouses_in_same_channel(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - two warehouses in the same channel, both stocks for same variant at 0
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    stock_a, stock_b = Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=0),
            Stock(product_variant=variant, warehouse=other_warehouse, quantity=0),
        ]
    )

    # when - both stocks passed together
    trigger_out_of_stock_in_channel_events_for_stocks([stock_a, stock_b], site_settings)

    # then - both fire because there is no OTHER warehouse with availability
    # (each warehouse only sees the other, which is also at 0)
    assert mocked_out.call_count == 2


def test_bulk_warehouse_a_is_other_for_warehouse_b_stock(
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - warehouse A has variant X at 0 and variant Y at 5
    #         warehouse B has variant Y at 0
    # For variant X in warehouse A: warehouse B has no stock → fires
    # For variant Y in warehouse B: warehouse A has stock (qty=5) → does not fire
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    variant_x, variant_y = variants[0], variants[1]

    stock_a_x = Stock.objects.get(product_variant=variant_x, warehouse=warehouse)
    stock_a_x.quantity = 0
    stock_a_y = Stock.objects.get(product_variant=variant_y, warehouse=warehouse)
    stock_a_y.quantity = 5
    Stock.objects.bulk_update([stock_a_x, stock_a_y], ["quantity"])

    warehouse_b = Warehouse.objects.create(
        address=address.get_copy(),
        name="warehouse-b",
        slug="warehouse-b",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    warehouse_b.channels.add(channel_USD)
    stock_b_y = Stock.objects.create(
        product_variant=variant_y, warehouse=warehouse_b, quantity=0
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks(
        [stock_a_x, stock_b_y], site_settings
    )

    # then - only variant X fires (warehouse B has no stock for variant X)
    # variant Y does not fire (warehouse A has availability for variant Y)
    mocked_out.assert_called_once()
    assert mocked_out.call_args.args[0].variant_id == variant_x.id


def test_bulk_mixed_cc_and_non_cc_stocks(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - one non-C&C stock and one C&C stock, both at 0
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    mocked_out_cc = mocker.patch(OUT_CC)
    cc_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="cc",
        slug="cc",
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
    )
    cc_warehouse.channels.add(channel_USD)
    stock_non_cc, stock_cc = Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=0),
            Stock(product_variant=variant, warehouse=cc_warehouse, quantity=0),
        ]
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks(
        [stock_non_cc, stock_cc], site_settings
    )

    # then - each fires in its own event type
    mocked_out.assert_called_once()
    assert mocked_out.call_args.args[0].variant_id == variant.id
    mocked_out_cc.assert_called_once()
    assert mocked_out_cc.call_args.args[0].variant_id == variant.id


def test_bulk_multi_channel_fires_per_channel_independently(
    variant, warehouse, channel_USD, channel_PLN, address, site_settings, mocker
):
    # given - warehouse in both channels; another warehouse with stock only in USD
    mocked_out = mocker.patch(OUT_IN_CHANNEL)
    warehouse.channels.add(channel_PLN)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=0
    )
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="usd-only",
        slug="usd-only",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    Stock.objects.create(product_variant=variant, warehouse=other_warehouse, quantity=5)

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock], site_settings)

    # then - fires only for PLN (USD has other warehouse with stock)
    mocked_out.assert_called_once()
    assert mocked_out.call_args.args[0].channel_slug == channel_PLN.slug


def test_bulk_empty_list_does_not_fire(site_settings, mocker):
    # given
    mocked_out = mocker.patch(OUT_IN_CHANNEL)

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([], site_settings)

    # then
    mocked_out.assert_not_called()
