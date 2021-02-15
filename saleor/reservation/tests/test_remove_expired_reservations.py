from io import StringIO

from django.core.management import call_command

from ..models import Reservation
from ..stock import remove_expired_reservations


def test_management_command_removes_expired_reservations(
    variant_with_expired_stock_reservation,
):
    call_command("remove_expired_stock_reservations", stdout=StringIO())
    assert not Reservation.objects.exists()


def test_management_command_excludes_active_reservations(variant_with_reserved_stock):
    call_command("remove_expired_stock_reservations", stdout=StringIO())
    assert Reservation.objects.exists()


def test_util_removes_expired_reservations(variant_with_expired_stock_reservation):
    remove_expired_reservations()
    assert not Reservation.objects.exists()


def test_util_excludes_active_reservations(variant_with_reserved_stock):
    remove_expired_reservations()
    assert Reservation.objects.exists()
