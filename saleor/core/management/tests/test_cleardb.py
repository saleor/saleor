import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from ....account.models import User
from ....checkout.models import Checkout
from ....order.models import Order
from ....product.models import Category, Product
from ....shipping.models import ShippingZone


@pytest.mark.django_db
def test_cleardb_raises_error_when_not_in_debug_mode(settings):
    # given
    settings.DEBUG = False

    # when / then
    with pytest.raises(CommandError):
        call_command("cleardb")


@pytest.mark.django_db
def test_cleardb_runs_in_debug_false_with_force_flag(settings):
    # given
    settings.DEBUG = False

    # when / then - should not raise
    call_command("cleardb", force=True)


@pytest.mark.django_db
def test_cleardb_removes_orders(settings, order):
    # given
    settings.DEBUG = True
    assert Order.objects.exists()

    # when
    call_command("cleardb")

    # then
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_cleardb_removes_checkouts(settings, checkout):
    # given
    settings.DEBUG = True
    assert Checkout.objects.exists()

    # when
    call_command("cleardb")

    # then
    assert not Checkout.objects.exists()


@pytest.mark.django_db
def test_cleardb_removes_products_and_categories(settings, product):
    # given
    settings.DEBUG = True
    assert Product.objects.exists()
    assert Category.objects.exists()

    # when
    call_command("cleardb")

    # then
    assert not Product.objects.exists()
    assert not Category.objects.exists()


@pytest.mark.django_db
def test_cleardb_removes_customers_but_preserves_staff(
    settings, customer_user, staff_user
):
    # given
    settings.DEBUG = True
    assert User.objects.filter(is_staff=False, is_superuser=False).exists()
    assert User.objects.filter(is_staff=True).exists()

    # when
    call_command("cleardb")

    # then
    assert not User.objects.filter(is_staff=False, is_superuser=False).exists()
    assert User.objects.filter(is_staff=True).exists()


@pytest.mark.django_db
def test_cleardb_delete_staff_flag_removes_staff_but_preserves_superuser(
    settings, staff_user, superuser
):
    # given
    settings.DEBUG = True
    assert User.objects.filter(is_staff=True, is_superuser=False).exists()
    assert User.objects.filter(is_superuser=True).exists()

    # when
    call_command("cleardb", delete_staff=True)

    # then
    assert not User.objects.filter(is_staff=True, is_superuser=False).exists()
    assert User.objects.filter(is_superuser=True).exists()


@pytest.mark.django_db
def test_cleardb_removes_shipping_zones(settings, shipping_zone):
    # given
    settings.DEBUG = True
    assert ShippingZone.objects.exists()

    # when
    call_command("cleardb")

    # then
    assert not ShippingZone.objects.exists()