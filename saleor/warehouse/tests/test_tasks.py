from datetime import timedelta

from django.utils import timezone

from ..models import Reservation
from ..tasks import delete_expired_reservations_task


def test_delete_expired_reservations_task_deletes_expired_reservations(
    checkout_line_with_reservation_in_many_stocks,
):
    Reservation.objects.update(reserved_until=timezone.now() - timedelta(seconds=1))
    delete_expired_reservations_task()
    assert not Reservation.objects.exists()


def test_delete_expired_reservations_task_skips_active_reservations(
    checkout_line_with_reservation_in_many_stocks,
):
    reservations_count = Reservation.objects.count()
    Reservation.objects.update(reserved_until=timezone.now() + timedelta(seconds=1))
    delete_expired_reservations_task()
    assert Reservation.objects.count() == reservations_count
