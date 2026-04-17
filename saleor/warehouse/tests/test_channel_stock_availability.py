from .. import WarehouseClickAndCollectOption
from ..channel_stock_availability import (
    trigger_back_in_stock_in_channel_events,
    trigger_out_of_stock_in_channel_events,
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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

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
    trigger_back_in_stock_in_channel_events(stock, site_settings)

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
    trigger_back_in_stock_in_channel_events(stock, site_settings)

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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

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
    trigger_out_of_stock_in_channel_events(stock, site_settings)

    # then
    args, kwargs = mocked_out.call_args
    assert args[1] is site_settings
    assert kwargs["requestor"] is None
    assert kwargs["webhooks"] is None
