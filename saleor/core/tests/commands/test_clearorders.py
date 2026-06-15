import pytest
from django.core.management import call_command

from ....checkout.models import Checkout, CheckoutDelivery


@pytest.mark.django_db
def test_delete_checkouts_with_checkout_delivery(checkout, checkout_delivery):
    # given
    delivery = checkout_delivery(checkout)
    assert Checkout.objects.filter(pk=checkout.pk).exists()
    assert CheckoutDelivery.objects.filter(pk=delivery.pk).exists()

    # when
    call_command("clearorders")

    # then
    assert not Checkout.objects.filter(pk=checkout.pk).exists()
    assert not CheckoutDelivery.objects.filter(pk=delivery.pk).exists()
