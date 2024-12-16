import pytest

from ...checkout.fetch import fetch_checkout_lines
from ...core.exceptions import InsufficientStock
from ...shipping.models import ShippingZone
from ..availability import (
    _get_available_quantity,
    check_stock_quantity,
    check_stock_quantity_bulk,
    get_available_quantity,
)
from ..models import Allocation

COUNTRY_CODE = "US"


def test_check_stock_quantity(variant_with_many_stocks, channel_USD):
    assert (
        check_stock_quantity(
            variant_with_many_stocks, COUNTRY_CODE, channel_USD.slug, 7
        )
        is None
    )


def test_check_stock_quantity_out_of_stock(variant_with_many_stocks, channel_USD):
    with pytest.raises(InsufficientStock):
        check_stock_quantity(
            variant_with_many_stocks, COUNTRY_CODE, channel_USD.slug, 8
        )


def test_check_stock_quantity_with_allocations(
    variant_with_many_stocks,
    order_line_with_allocation_in_many_stocks,
    order_line_with_one_allocation,
    channel_USD,
):
    assert (
        check_stock_quantity(
            variant_with_many_stocks, COUNTRY_CODE, channel_USD.slug, 3
        )
        is None
    )


def test_check_stock_quantity_with_allocations_out_of_stock(
    variant_with_many_stocks, order_line_with_allocation_in_many_stocks, channel_USD
):
    with pytest.raises(InsufficientStock):
        check_stock_quantity(
            variant_with_many_stocks, COUNTRY_CODE, channel_USD.slug, 5
        )


def test_check_stock_quantity_with_reservations(
    variant_with_many_stocks,
    checkout_line_with_reservation_in_many_stocks,
    checkout_line_with_one_reservation,
    channel_USD,
):
    assert (
        check_stock_quantity(
            variant_with_many_stocks,
            COUNTRY_CODE,
            channel_USD.slug,
            2,
            check_reservations=True,
        )
        is None
    )


def test_check_stock_quantity_with_reservations_excluding_given_checkout_lines(
    variant_with_many_stocks,
    checkout_line_with_reservation_in_many_stocks,
    checkout_line_with_one_reservation,
    channel_USD,
):
    assert (
        check_stock_quantity(
            variant_with_many_stocks,
            COUNTRY_CODE,
            channel_USD.slug,
            7,
            [
                checkout_line_with_reservation_in_many_stocks,
                checkout_line_with_one_reservation,
            ],
            check_reservations=True,
        )
        is None
    )


def test_check_stock_quantity_without_stocks(variant_with_many_stocks, channel_USD):
    variant_with_many_stocks.stocks.all().delete()
    with pytest.raises(InsufficientStock):
        check_stock_quantity(
            variant_with_many_stocks, COUNTRY_CODE, channel_USD.slug, 1
        )


def test_check_stock_quantity_without_one_stock(variant_with_many_stocks, channel_USD):
    variant_with_many_stocks.stocks.get(quantity=3).delete()
    assert (
        check_stock_quantity(
            variant_with_many_stocks, COUNTRY_CODE, channel_USD.slug, 4
        )
        is None
    )


def test_get_available_quantity(variant_with_many_stocks, channel_USD):
    available_quantity = get_available_quantity(
        variant_with_many_stocks, COUNTRY_CODE, channel_USD.slug
    )
    assert available_quantity == 7


def test_get_available_quantity_without_allocation(order_line, stock, channel_USD):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    available_quantity = get_available_quantity(
        order_line.variant, COUNTRY_CODE, channel_USD.slug
    )
    assert available_quantity == stock.quantity


def test_get_available_quantity_with_allocations(
    variant_with_many_stocks,
    order_line_with_allocation_in_many_stocks,
    order_line_with_one_allocation,
    channel_USD,
):
    available_quantity = get_available_quantity(
        variant_with_many_stocks, COUNTRY_CODE, channel_USD.slug
    )
    assert available_quantity == 3


def test_get_available_quantity_with_reservations(
    variant_with_many_stocks,
    checkout_line_with_reservation_in_many_stocks,
    checkout_line_with_one_reservation,
    channel_USD,
):
    available_quantity = get_available_quantity(
        variant_with_many_stocks,
        COUNTRY_CODE,
        channel_USD.slug,
        check_reservations=True,
    )
    assert available_quantity == 2


def test_get_available_quantity_with_allocations_and_reservations(
    variant_with_many_stocks,
    order_line_with_one_allocation,
    checkout_line_with_one_reservation,
    channel_USD,
):
    available_quantity = get_available_quantity(
        variant_with_many_stocks,
        COUNTRY_CODE,
        channel_USD.slug,
        check_reservations=True,
    )
    assert available_quantity == 4


def test_get_available_quantity_with_reservations_excluding_given_checkout_lines(
    variant_with_many_stocks,
    checkout_line_with_reservation_in_many_stocks,
    checkout_line_with_one_reservation,
    channel_USD,
):
    available_quantity = get_available_quantity(
        variant_with_many_stocks,
        COUNTRY_CODE,
        channel_USD.slug,
        [
            checkout_line_with_reservation_in_many_stocks,
            checkout_line_with_one_reservation,
        ],
        check_reservations=True,
    )
    assert available_quantity == 7


def test_get_available_quantity_without_stocks(variant_with_many_stocks, channel_USD):
    variant_with_many_stocks.stocks.all().delete()
    available_quantity = get_available_quantity(
        variant_with_many_stocks, COUNTRY_CODE, channel_USD.slug
    )
    assert available_quantity == 0


def test_check_stock_quantity_bulk(variant_with_many_stocks, channel_USD):
    variant = variant_with_many_stocks
    country_code = "US"
    available_quantity = _get_available_quantity(variant.stocks.all())
    global_quantity_limit = 50

    # test that it doesn't raise error for available quantity
    assert (
        check_stock_quantity_bulk(
            [variant_with_many_stocks],
            country_code,
            [available_quantity],
            channel_USD.slug,
            global_quantity_limit,
        )
        is None
    )

    # test that it raises an error for exceeded quantity
    with pytest.raises(InsufficientStock):
        check_stock_quantity_bulk(
            [variant_with_many_stocks],
            country_code,
            [available_quantity + 1],
            channel_USD,
            global_quantity_limit,
        )

    # test that it raises an error if no stocks are found
    variant.stocks.all().delete()
    with pytest.raises(InsufficientStock):
        check_stock_quantity_bulk(
            [variant_with_many_stocks],
            country_code,
            [available_quantity],
            channel_USD.slug,
            global_quantity_limit,
        )

    # test that it doesn't raise an error if variant.track_inventory is False
    variant.track_inventory = False
    variant.save(update_fields=["track_inventory"])
    check_stock_quantity_bulk(
        [variant],
        country_code,
        [available_quantity],
        channel_USD.slug,
        global_quantity_limit,
    )


def test_check_stock_quantity_bulk_no_channel_shipping_zones(
    variant_with_many_stocks, channel_USD
):
    variant = variant_with_many_stocks
    country_code = "US"
    available_quantity = _get_available_quantity(variant.stocks.all())
    global_quantity_limit = 50

    channel_USD.shipping_zones.clear()

    with pytest.raises(InsufficientStock):
        check_stock_quantity_bulk(
            [variant_with_many_stocks],
            country_code,
            [available_quantity],
            channel_USD.slug,
            global_quantity_limit,
        )


def test_check_stock_quantity_bulk_with_reservations(
    variant_with_many_stocks,
    checkout_line_with_reservation_in_many_stocks,
    checkout_line_with_one_reservation,
    channel_USD,
):
    variant = variant_with_many_stocks
    country_code = "US"
    available_quantity = get_available_quantity(
        variant,
        country_code,
        channel_USD.slug,
        check_reservations=True,
    )
    global_quantity_limit = 50

    # test that it doesn't raise error for available quantity
    assert (
        check_stock_quantity_bulk(
            [variant_with_many_stocks],
            country_code,
            [available_quantity],
            channel_USD.slug,
            global_quantity_limit,
            check_reservations=True,
        )
        is None
    )

    # test that it raises an error for exceeded quantity
    with pytest.raises(InsufficientStock):
        check_stock_quantity_bulk(
            [variant_with_many_stocks],
            country_code,
            [available_quantity + 1],
            channel_USD.slug,
            global_quantity_limit,
            check_reservations=True,
        )

    # test that it passes if checkout lines are excluded
    checkout_lines, _ = fetch_checkout_lines(
        checkout_line_with_one_reservation.checkout
    )
    assert (
        check_stock_quantity_bulk(
            [variant_with_many_stocks],
            country_code,
            [available_quantity + 1],
            channel_USD.slug,
            global_quantity_limit,
            existing_lines=checkout_lines,
            check_reservations=True,
        )
        is None
    )


@pytest.mark.parametrize(
    ("first_wh_qt", "secont_wh_qt"),
    [
        (30, 30),
        (-100, 30),
        (30, -100),
    ],
)
def test_check_stock_quantity_bulk_separate_stocks_different_sz_with_the_same_country(
    first_wh_qt,
    secont_wh_qt,
    variant_with_many_stocks_different_shipping_zones,
    channel_USD,
    shipping_zones,
):
    # given
    for zone in shipping_zones:
        zone.countries = [channel_USD.default_country]
    ShippingZone.objects.bulk_update(shipping_zones, ["countries"])

    variant = variant_with_many_stocks_different_shipping_zones
    quantity_to_check = 15
    global_quantity_limit = 50
    assert len(variant.stocks.all()) == 2
    stock_from_first_sz, stock_from_second_sz = variant.stocks.all()

    stock_from_first_sz.quantity = first_wh_qt
    stock_from_first_sz.save()

    stock_from_second_sz.quantity = secont_wh_qt
    stock_from_second_sz.save()

    # when
    # test that it doesn't raise error for available quantity
    assert (
        check_stock_quantity_bulk(
            [variant],
            channel_USD.default_country,
            [quantity_to_check],
            channel_USD.slug,
            global_quantity_limit,
        )
        is None
    )


def test_check_stock_quantity_bulk_separate_stock_only_in_cc_warehouse(
    variant, warehouse_for_cc, channel_USD
):
    # given
    variant.stocks.create(warehouse=warehouse_for_cc, quantity=10)

    quantity_to_check = 5
    global_quantity_limit = 50
    assert len(variant.stocks.all()) == 1

    # when
    # test that it doesn't raise error for available quantity
    assert (
        check_stock_quantity_bulk(
            [variant],
            channel_USD.default_country,
            [quantity_to_check],
            channel_USD.slug,
            global_quantity_limit,
        )
        is None
    )


@pytest.mark.parametrize(
    ("cc_qt", "wh_qt"),
    [
        (10, 10),
        (-100, 10),
        (10, -100),
    ],
)
def test_check_stock_quantity_bulk_separate_stocks_with_cc_warehouse_and_warehouse(
    cc_qt, wh_qt, variant, warehouse_for_cc, channel_USD, warehouse
):
    # given
    variant.stocks.create(warehouse=warehouse_for_cc, quantity=cc_qt)
    variant.stocks.create(warehouse=warehouse, quantity=wh_qt)

    quantity_to_check = 5
    global_quantity_limit = 50
    assert len(variant.stocks.all()) == 2

    # when
    # test that it doesn't raise error for available quantity
    assert (
        check_stock_quantity_bulk(
            [variant],
            channel_USD.default_country,
            [quantity_to_check],
            channel_USD.slug,
            global_quantity_limit,
        )
        is None
    )
