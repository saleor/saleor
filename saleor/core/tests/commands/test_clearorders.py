import pytest
from django.core.management import call_command

from ....checkout.models import Checkout, CheckoutDelivery


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("_case", "assign_delivery"),
    [
        # These two cases cause two different types of FK-checks
        # which can cause PostgreSQL to refuse to delete these checkouts.
        # Thus we need these two cases to ensure both FK checks are properly
        # handled.
        ("delivery_not_assigned", False),
        ("delivery_assigned_to_checkout", True),
    ],
)
def test_delete_checkouts_with_checkout_delivery(
    _case, checkout, checkout_delivery, assign_delivery
):
    # given
    delivery = checkout_delivery(checkout)
    if assign_delivery:
        checkout.assigned_delivery = delivery
        checkout.save(update_fields=["assigned_delivery"])

    assert Checkout.objects.filter(pk=checkout.pk).exists()
    assert CheckoutDelivery.objects.filter(pk=delivery.pk).exists()

    # when
    call_command("clearorders")

    # then
    assert not Checkout.objects.filter(pk=checkout.pk).exists()
    assert not CheckoutDelivery.objects.filter(pk=delivery.pk).exists()
