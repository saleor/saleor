from datetime import timedelta

import pytest
from django.utils import timezone

from ..models import PreorderReservation, Reservation
from ..tasks import (
    delete_expired_reservations_task,
    update_stocks_quantity_allocated_task,
)


def test_delete_expired_reservations_task_deletes_expired_stock_reservations(
    checkout_line_with_reservation_in_many_stocks,
):
    Reservation.objects.update(reserved_until=timezone.now() - timedelta(seconds=1))
    delete_expired_reservations_task()
    assert not Reservation.objects.exists()


def test_delete_expired_reservations_task_skips_active_stock_reservations(
    checkout_line_with_reservation_in_many_stocks,
):
    reservations_count = Reservation.objects.count()
    Reservation.objects.update(reserved_until=timezone.now() + timedelta(seconds=1))
    delete_expired_reservations_task()
    assert Reservation.objects.count() == reservations_count


def test_delete_expired_reservations_task_deletes_expired_preorder_reservations(
    checkout_line_with_reserved_preorder_item,
):
    PreorderReservation.objects.update(
        reserved_until=timezone.now() - timedelta(seconds=1)
    )
    delete_expired_reservations_task()
    assert not PreorderReservation.objects.exists()


def test_delete_expired_reservations_task_skips_active_preorder_reservations(
    checkout_line_with_reserved_preorder_item,
):
    reservations_count = PreorderReservation.objects.count()
    PreorderReservation.objects.update(
        reserved_until=timezone.now() + timedelta(seconds=1)
    )
    delete_expired_reservations_task()
    assert PreorderReservation.objects.count() == reservations_count


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
