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
    stock_infos = mocked_out.call_args.args[0]
    assert stock_infos == [
        VariantChannelStockInfo(variant_id=variant.id, channel_slug=channel_USD.slug)
    ]
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
    stock_infos = mocked_out_cc.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].channel_slug == channel_USD.slug
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
    stock_infos = mocked_out.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].channel_slug == channel_PLN.slug


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
    stock_infos = mocked_out.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].channel_slug == channel_USD.slug


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


def test_bulk_out_of_stock_fires_for_multiple_stocks_in_same_warehouse(
    product_with_two_variants, warehouse, channel_USD, site_settings, mocker
):
    # given - two variants in the same warehouse, both at 0
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    for stock in stocks:
        stock.quantity = 0
    Stock.objects.bulk_update(stocks, ["quantity"])

    # when
    trigger_out_of_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then - one batched call carrying one info per (variant, channel)
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    fired_variant_ids = {info.variant_id for info in stock_infos}
    assert fired_variant_ids == {variants[0].id, variants[1].id}


def test_bulk_out_of_stock_does_not_fire_when_other_warehouse_covers_all_variants(
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - another non-C&C warehouse in the same channel has stock for both
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)
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

    # then
    mocked_trigger.assert_not_called()


def test_bulk_out_of_stock_fires_selectively_when_other_warehouse_covers_only_one_variant(
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - another warehouse has stock only for variants[0], not variants[1]
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)
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

    # then
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].variant_id == variants[1].id


def test_bulk_out_of_stock_deduplicates_same_variant_across_warehouses_in_channel(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - two warehouses in the same channel, same variant, both at 0
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)
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

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock_a, stock_b], site_settings)

    # then - fires once per (variant, channel)
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].variant_id == variant.id
    assert stock_infos[0].channel_slug == channel_USD.slug


def test_bulk_out_of_stock_warehouse_a_is_other_for_warehouse_b_stock(
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - warehouse A has variant X (at 0) and variant Y (qty 5)
    #         warehouse B has variant Y at 0
    # For variant X in warehouse A: warehouse B has no stock → fires
    # For variant Y in warehouse B: warehouse A has stock → does not fire
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)
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

    # then
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].variant_id == variant_x.id


def test_bulk_out_of_stock_mixed_cc_and_non_cc_stocks(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - one non-C&C stock and one C&C stock, both at 0
    mocked_non_cc = mocker.patch(OUT_IN_CHANNEL)
    mocked_cc = mocker.patch(OUT_CC)
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
    mocked_non_cc.assert_called_once()
    non_cc_infos = mocked_non_cc.call_args.args[0]
    assert len(non_cc_infos) == 1
    assert non_cc_infos[0].variant_id == variant.id
    mocked_cc.assert_called_once()
    cc_infos = mocked_cc.call_args.args[0]
    assert len(cc_infos) == 1
    assert cc_infos[0].variant_id == variant.id


def test_bulk_out_of_stock_multi_channel_fires_per_channel_independently(
    variant, warehouse, channel_USD, channel_PLN, address, site_settings, mocker
):
    # given - warehouse in both channels; another warehouse with stock only in USD
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)
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
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].channel_slug == channel_PLN.slug


def test_bulk_out_of_stock_empty_list_does_not_fire(site_settings, mocker):
    # given
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([], site_settings)

    # then
    mocked_trigger.assert_not_called()


def test_bulk_out_of_stock_two_different_variants_fires_for_each(
    product_with_two_variants, warehouse, channel_USD, site_settings, mocker
):
    # given - two different variants in the same warehouse, both at 0, no other
    # warehouse in the channel
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    for stock in stocks:
        stock.quantity = 0
    Stock.objects.bulk_update(stocks, ["quantity"])

    # when
    trigger_out_of_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    fired_pairs = {(info.variant_id, info.channel_slug) for info in stock_infos}
    assert fired_pairs == {
        (variants[0].id, channel_USD.slug),
        (variants[1].id, channel_USD.slug),
    }


def test_bulk_out_of_stock_deduplicates_same_variant_multiple_warehouses_and_channels(
    variant, warehouse, channel_USD, channel_PLN, address, site_settings, mocker
):
    # given - same variant in two warehouses, both in two channels, both at 0
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)
    warehouse.channels.add(channel_PLN)
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD, channel_PLN)
    stock_a, stock_b = Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=0),
            Stock(product_variant=variant, warehouse=other_warehouse, quantity=0),
        ]
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks([stock_a, stock_b], site_settings)

    # then - fires once per channel (2 channels), not once per stock
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 2
    fired_slugs = {info.channel_slug for info in stock_infos}
    assert fired_slugs == {channel_USD.slug, channel_PLN.slug}


def test_bulk_out_of_stock_different_variants_partial_coverage_by_other_warehouse(
    product_with_two_variants,
    warehouse,
    channel_USD,
    channel_PLN,
    address,
    site_settings,
    mocker,
):
    # given - variant X is covered by other warehouse in USD but not PLN
    #         variant Y has no coverage in either channel
    mocked_trigger = mocker.patch(OUT_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    variant_x, variant_y = variants[0], variants[1]

    warehouse.channels.add(channel_PLN)
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
    # other warehouse only in USD, only has stock for variant X
    other_warehouse.channels.add(channel_USD)
    Stock.objects.create(
        product_variant=variant_x, warehouse=other_warehouse, quantity=5
    )

    # when
    trigger_out_of_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then
    # variant X: covered in USD, uncovered in PLN → fires only for PLN
    # variant Y: uncovered everywhere → fires for both USD and PLN
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 3
    fired_pairs = {(info.variant_id, info.channel_slug) for info in stock_infos}
    assert fired_pairs == {
        (variant_x.id, channel_PLN.slug),
        (variant_y.id, channel_USD.slug),
        (variant_y.id, channel_PLN.slug),
    }


def test_bulk_back_in_stock_fires_for_multiple_stocks_in_same_warehouse(
    product_with_two_variants, warehouse, channel_USD, site_settings, mocker
):
    # given - two variants in the same warehouse, both back at positive qty
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    # stocks are already at qty 10 from the fixture
    for stock in stocks:
        stock.quantity = 10
    Stock.objects.bulk_update(stocks, ["quantity"])

    # when
    trigger_back_in_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then - one batched call carrying one info per (variant, channel)
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    fired_variant_ids = {info.variant_id for info in stock_infos}
    assert fired_variant_ids == {variants[0].id, variants[1].id}


def test_bulk_back_in_stock_does_not_fire_when_other_warehouse_covers_all_variants(
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - another non-C&C warehouse in the same channel already has stock
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    for stock in stocks:
        stock.quantity = 10
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
    trigger_back_in_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then - other warehouse already had stock, these aren't "first back"
    mocked_trigger.assert_not_called()


def test_bulk_back_in_stock_fires_selectively_when_other_warehouse_covers_only_one_variant(
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - another warehouse has stock only for variants[0], not variants[1]
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    for stock in stocks:
        stock.quantity = 10
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
    trigger_back_in_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then - only variants[1] fires (variants[0] was already covered elsewhere)
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].variant_id == variants[1].id


def test_bulk_back_in_stock_deduplicates_same_variant_across_warehouses_in_channel(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - two warehouses in the same channel, same variant, both back at positive
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    stock_a, stock_b = Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=10),
            Stock(product_variant=variant, warehouse=other_warehouse, quantity=10),
        ]
    )

    # when
    trigger_back_in_stock_in_channel_events_for_stocks(
        [stock_a, stock_b], site_settings
    )

    # then - fires once per (variant, channel)
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].variant_id == variant.id
    assert stock_infos[0].channel_slug == channel_USD.slug


def test_bulk_back_in_stock_warehouse_a_is_other_for_warehouse_b_stock(
    product_with_two_variants,
    warehouse,
    channel_USD,
    address,
    site_settings,
    mocker,
):
    # given - warehouse A has variant X back (qty 10) and variant Y with qty 5
    #         warehouse B has variant Y back (qty 10)
    # For variant X in warehouse A: warehouse B has no stock for X → fires
    # For variant Y in warehouse B: warehouse A has stock for Y → does not fire
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    variant_x, variant_y = variants[0], variants[1]

    stock_a_x = Stock.objects.get(product_variant=variant_x, warehouse=warehouse)
    stock_a_x.quantity = 10
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
        product_variant=variant_y, warehouse=warehouse_b, quantity=10
    )

    # when
    trigger_back_in_stock_in_channel_events_for_stocks(
        [stock_a_x, stock_b_y], site_settings
    )

    # then
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].variant_id == variant_x.id


def test_bulk_back_in_stock_mixed_cc_and_non_cc_stocks(
    variant, warehouse, channel_USD, address, site_settings, mocker
):
    # given - one non-C&C stock and one C&C stock, both back at positive qty
    mocked_non_cc = mocker.patch(BACK_IN_CHANNEL)
    mocked_cc = mocker.patch(BACK_CC)
    cc_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="cc",
        slug="cc",
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
    )
    cc_warehouse.channels.add(channel_USD)
    stock_non_cc, stock_cc = Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=10),
            Stock(product_variant=variant, warehouse=cc_warehouse, quantity=10),
        ]
    )

    # when
    trigger_back_in_stock_in_channel_events_for_stocks(
        [stock_non_cc, stock_cc], site_settings
    )

    # then - each fires in its own event type
    mocked_non_cc.assert_called_once()
    non_cc_infos = mocked_non_cc.call_args.args[0]
    assert len(non_cc_infos) == 1
    assert non_cc_infos[0].variant_id == variant.id
    mocked_cc.assert_called_once()
    cc_infos = mocked_cc.call_args.args[0]
    assert len(cc_infos) == 1
    assert cc_infos[0].variant_id == variant.id


def test_bulk_back_in_stock_multi_channel_fires_per_channel_independently(
    variant, warehouse, channel_USD, channel_PLN, address, site_settings, mocker
):
    # given - warehouse in both channels; another warehouse with stock only in USD
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)
    warehouse.channels.add(channel_PLN)
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=10
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
    trigger_back_in_stock_in_channel_events_for_stocks([stock], site_settings)

    # then - fires only for PLN (USD already has other warehouse with stock)
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 1
    assert stock_infos[0].channel_slug == channel_PLN.slug


def test_bulk_back_in_stock_empty_list_does_not_fire(site_settings, mocker):
    # given
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)

    # when
    trigger_back_in_stock_in_channel_events_for_stocks([], site_settings)

    # then
    mocked_trigger.assert_not_called()


def test_bulk_back_in_stock_two_different_variants_fires_for_each(
    product_with_two_variants, warehouse, channel_USD, site_settings, mocker
):
    # given - two different variants in the same warehouse, both back at positive,
    # no other warehouse in the channel
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    for stock in stocks:
        stock.quantity = 10
    Stock.objects.bulk_update(stocks, ["quantity"])

    # when
    trigger_back_in_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    fired_pairs = {(info.variant_id, info.channel_slug) for info in stock_infos}
    assert fired_pairs == {
        (variants[0].id, channel_USD.slug),
        (variants[1].id, channel_USD.slug),
    }


def test_bulk_back_in_stock_deduplicates_same_variant_multiple_warehouses_and_channels(
    variant, warehouse, channel_USD, channel_PLN, address, site_settings, mocker
):
    # given - same variant in two warehouses, both in two channels, both back at positive
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)
    warehouse.channels.add(channel_PLN)
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD, channel_PLN)
    stock_a, stock_b = Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=10),
            Stock(product_variant=variant, warehouse=other_warehouse, quantity=10),
        ]
    )

    # when
    trigger_back_in_stock_in_channel_events_for_stocks(
        [stock_a, stock_b], site_settings
    )

    # then - fires once per channel, not once per stock
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 2
    fired_slugs = {info.channel_slug for info in stock_infos}
    assert fired_slugs == {channel_USD.slug, channel_PLN.slug}


def test_bulk_back_in_stock_different_variants_partial_coverage_by_other_warehouse(
    product_with_two_variants,
    warehouse,
    channel_USD,
    channel_PLN,
    address,
    site_settings,
    mocker,
):
    # given - variant X is covered by other warehouse in USD but not PLN
    #         variant Y has no coverage in either channel
    mocked_trigger = mocker.patch(BACK_IN_CHANNEL)
    variants = list(product_with_two_variants.variants.all())
    variant_x, variant_y = variants[0], variants[1]

    warehouse.channels.add(channel_PLN)
    stocks = list(
        Stock.objects.filter(product_variant__in=variants, warehouse=warehouse)
    )
    for stock in stocks:
        stock.quantity = 10
    Stock.objects.bulk_update(stocks, ["quantity"])

    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    # other warehouse only in USD, only has stock for variant X
    other_warehouse.channels.add(channel_USD)
    Stock.objects.create(
        product_variant=variant_x, warehouse=other_warehouse, quantity=5
    )

    # when
    trigger_back_in_stock_in_channel_events_for_stocks(stocks, site_settings)

    # then
    # variant X: USD already covered by other warehouse, PLN uncovered → fires only for PLN
    # variant Y: uncovered everywhere → fires for both USD and PLN
    mocked_trigger.assert_called_once()
    stock_infos = mocked_trigger.call_args.args[0]
    assert len(stock_infos) == 3
    fired_pairs = {(info.variant_id, info.channel_slug) for info in stock_infos}
    assert fired_pairs == {
        (variant_x.id, channel_PLN.slug),
        (variant_y.id, channel_USD.slug),
        (variant_y.id, channel_PLN.slug),
    }
