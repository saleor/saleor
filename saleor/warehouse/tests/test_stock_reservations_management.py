from datetime import timedelta

import pytest
from django.utils import timezone

from ...channel import AllocationStrategy
from ...checkout.models import Checkout
from ...core.exceptions import InsufficientStock
from ..models import ChannelWarehouse, Reservation, Stock, Warehouse
from ..reservations import reserve_stocks

COUNTRY_CODE = "US"
RESERVATION_LENGTH = 5


def test_reserve_stocks(checkout_line, channel_USD):
    checkout_line.quantity = 5
    checkout_line.save()

    stock = Stock.objects.get(product_variant=checkout_line.variant)
    stock.quantity = 10
    stock.save(update_fields=["quantity"])

    reserve_stocks(
        [checkout_line],
        [checkout_line.variant],
        COUNTRY_CODE,
        channel_USD,
        RESERVATION_LENGTH,
    )

    stock.refresh_from_db()
    assert stock.quantity == 10
    reservation = Reservation.objects.get(checkout_line=checkout_line, stock=stock)
    assert reservation.quantity_reserved == 5
    assert reservation.reserved_until > timezone.now() + timedelta(minutes=1)


def test_stocks_reservation_skips_prev_reservation_delete_if_replace_is_disabled(
    checkout_line, assert_num_queries, channel_USD
):
    with assert_num_queries(3):
        reserve_stocks(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD,
            RESERVATION_LENGTH,
            replace=False,
        )

    with assert_num_queries(4):
        reserve_stocks(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD,
            RESERVATION_LENGTH,
        )


def test_multiple_stocks_reserved_if_single_stock_is_not_enough_highest_stock_strategy(
    checkout_line, warehouse, shipping_zone, channel_USD
):
    checkout_line.quantity = 5
    checkout_line.save()

    stock = Stock.objects.get(product_variant=checkout_line.variant)
    stock.quantity = 3
    stock.save(update_fields=["quantity"])

    secondary_warehouse = Warehouse.objects.create(
        address=warehouse.address,
        name="Warehouse 2",
        slug="warehouse-2",
        email=warehouse.email,
    )
    secondary_warehouse.shipping_zones.add(shipping_zone)
    secondary_warehouse.channels.add(channel_USD)
    secondary_warehouse.save()

    secondary_stock = Stock.objects.create(
        warehouse=secondary_warehouse, product_variant=stock.product_variant, quantity=2
    )

    reserve_stocks(
        [checkout_line],
        [checkout_line.variant],
        COUNTRY_CODE,
        channel_USD,
        RESERVATION_LENGTH,
    )

    stock.refresh_from_db()
    assert stock.quantity == 3

    reservation = Reservation.objects.get(checkout_line=checkout_line, stock=stock)
    assert reservation.quantity_reserved == 3
    assert reservation.reserved_until > timezone.now() + timedelta(minutes=1)

    second_reservation = Reservation.objects.get(
        checkout_line=checkout_line, stock=secondary_stock
    )
    assert second_reservation.quantity_reserved == 2
    assert second_reservation.reserved_until > timezone.now() + timedelta(minutes=1)


def test_multiple_stocks_reserved_if_single_stock_is_not_enough_sorting_order_strategy(
    checkout_line, warehouse, shipping_zone, channel_USD
):
    # given
    # set the prioritize sorting order stratefy
    channel_USD.allocation_strategy = AllocationStrategy.PRIORITIZE_SORTING_ORDER
    channel_USD.save(update_fields=["allocation_strategy"])

    quantity = 5
    checkout_line.quantity = quantity
    checkout_line.save()

    stock = Stock.objects.get(product_variant=checkout_line.variant)
    stock_quantity = 4
    stock.quantity = stock_quantity
    stock.save(update_fields=["quantity"])

    secondary_warehouse = Warehouse.objects.create(
        address=warehouse.address,
        name="Warehouse 2",
        slug="warehouse-2",
        email=warehouse.email,
    )
    secondary_warehouse.shipping_zones.add(shipping_zone)
    secondary_warehouse.channels.add(channel_USD)
    secondary_warehouse.save()

    secondary_stock_quantity = 3
    secondary_stock = Stock.objects.create(
        warehouse=secondary_warehouse,
        product_variant=stock.product_variant,
        quantity=secondary_stock_quantity,
    )

    channel_warehouse_1 = stock.warehouse.channelwarehouse.first()
    channel_warehouse_2 = secondary_stock.warehouse.channelwarehouse.first()

    # set the warehouse order
    channel_warehouse_2.sort_order = 0
    channel_warehouse_1.sort_order = 1
    ChannelWarehouse.objects.bulk_update(
        [channel_warehouse_1, channel_warehouse_2], ["sort_order"]
    )

    # when
    reserve_stocks(
        [checkout_line],
        [checkout_line.variant],
        COUNTRY_CODE,
        channel_USD,
        RESERVATION_LENGTH,
    )

    # then
    stock.refresh_from_db()
    assert stock.quantity == stock_quantity

    second_reservation = Reservation.objects.get(
        checkout_line=checkout_line, stock=secondary_stock
    )
    assert second_reservation.quantity_reserved == secondary_stock_quantity
    assert second_reservation.reserved_until > timezone.now() + timedelta(minutes=1)

    reservation = Reservation.objects.get(checkout_line=checkout_line, stock=stock)
    assert reservation.quantity_reserved == quantity - secondary_stock_quantity
    assert reservation.reserved_until > timezone.now() + timedelta(minutes=1)


def test_stocks_reservation_removes_previous_reservations_for_checkout(
    checkout_line, channel_USD
):
    checkout_line.quantity = 5
    checkout_line.save()

    stock = Stock.objects.get(product_variant=checkout_line.variant)
    stock.quantity = 10
    stock.save(update_fields=["quantity"])

    previous_reservation = Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stock,
        quantity_reserved=5,
        reserved_until=timezone.now() + timedelta(hours=1),
    )

    reserve_stocks(
        [checkout_line],
        [checkout_line.variant],
        COUNTRY_CODE,
        channel_USD,
        RESERVATION_LENGTH,
    )

    with pytest.raises(Reservation.DoesNotExist):
        previous_reservation.refresh_from_db()


def test_stock_reservation_fails_if_there_is_not_enough_stock_available(
    checkout_line, channel_USD
):
    checkout_line.quantity = 5
    checkout_line.save()

    stock = Stock.objects.get(product_variant=checkout_line.variant)
    stock.quantity = 3
    stock.save(update_fields=["quantity"])

    with pytest.raises(InsufficientStock):
        reserve_stocks(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD,
            RESERVATION_LENGTH,
        )


def test_stock_reservation_fails_if_there_is_no_stock(checkout_line, channel_USD):
    checkout_line.quantity = 5
    checkout_line.save()

    Stock.objects.all().delete()

    with pytest.raises(InsufficientStock):
        reserve_stocks(
            [checkout_line],
            [checkout_line.variant],
            COUNTRY_CODE,
            channel_USD,
            RESERVATION_LENGTH,
        )


def test_stock_reservation_accounts_for_order_allocations(
    order_line_with_allocation_in_many_stocks, checkout, channel_USD
):
    variant = order_line_with_allocation_in_many_stocks.variant
    variant.stocks.update(quantity=3)  # 2 x 3 = 6

    checkout_line = checkout.lines.create(
        quantity=4,
        variant=variant,
    )

    with pytest.raises(InsufficientStock):
        reserve_stocks(
            [checkout_line],
            [variant],
            COUNTRY_CODE,
            channel_USD,
            RESERVATION_LENGTH,
        )


def test_stock_reservation_accounts_for_order_allocations_and_reservations(
    order_line_with_allocation_in_many_stocks, checkout, channel_USD
):
    variant = order_line_with_allocation_in_many_stocks.variant
    variant.stocks.update(quantity=3)  # 2 x 3 = 6

    other_checkout = Checkout.objects.create(
        currency=channel_USD.currency_code, channel=channel_USD
    )
    other_checkout.set_country("US", commit=True)
    other_checkout_line = checkout.lines.create(
        quantity=2,
        variant=variant,
    )

    Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=variant.stocks.order_by("pk").last(),
        quantity_reserved=2,
        reserved_until=timezone.now() + timedelta(hours=1),
    )

    checkout_line = checkout.lines.create(
        quantity=2,
        variant=variant,
    )

    with pytest.raises(InsufficientStock):
        reserve_stocks(
            [checkout_line],
            [variant],
            COUNTRY_CODE,
            channel_USD,
            RESERVATION_LENGTH,
        )
