import pytest
from django.core.management import call_command

from ....checkout.models import Checkout
from ....order.models import Order
from ....payment.models import Payment
from ....account.models import User


@pytest.mark.django_db
def test_clearorders_removes_orders(order):
    # given
    assert Order.objects.exists()

    # when
    call_command("clearorders")

    # then
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_clearorders_removes_checkouts(checkout):
    # given
    assert Checkout.objects.exists()

    # when
    call_command("clearorders")

    # then
    assert not Checkout.objects.exists()


@pytest.mark.django_db
def test_clearorders_preserves_customers_by_default(customer_user):
    # given
    assert User.objects.filter(is_staff=False, is_superuser=False).exists()

    # when
    call_command("clearorders")

    # then
    assert User.objects.filter(is_staff=False, is_superuser=False).exists()


@pytest.mark.django_db
def test_clearorders_delete_customers_flag_removes_customers(customer_user):
    # given
    assert User.objects.filter(is_staff=False, is_superuser=False).exists()

    # when
    call_command("clearorders", delete_customers=True)

    # then
    assert not User.objects.filter(is_staff=False, is_superuser=False).exists()