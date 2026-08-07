import pytest
from django.core.management import call_command

from ....account.models import User
from ....checkout.models import Checkout, CheckoutDelivery
from ....giftcard.models import GiftCard, GiftCardEvent
from ....order.models import Fulfillment, Order, OrderLine
from ....payment.models import Payment, TransactionItem
from ....product.models import Product
from ....warehouse.models import Allocation


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


@pytest.mark.django_db
def test_clearorders_removes_orders_with_lines_and_fulfillments(fulfilled_order):
    # given
    assert Order.objects.filter(pk=fulfilled_order.pk).exists()
    assert OrderLine.objects.filter(order_id=fulfilled_order.pk).exists()
    assert Fulfillment.objects.filter(order_id=fulfilled_order.pk).exists()

    # when
    call_command("clearorders")

    # then
    assert not Order.objects.exists()
    assert not OrderLine.objects.exists()
    assert not Fulfillment.objects.exists()


@pytest.mark.django_db
def test_clearorders_removes_payments_and_transaction_items(
    payment_dummy, transaction_item
):
    # given
    assert Payment.objects.filter(pk=payment_dummy.pk).exists()
    assert TransactionItem.objects.filter(pk=transaction_item.pk).exists()

    # when
    call_command("clearorders")

    # then
    assert not Payment.objects.exists()
    assert not TransactionItem.objects.exists()


@pytest.mark.django_db
def test_clearorders_removes_allocations(allocation):
    # given
    assert Allocation.objects.filter(pk=allocation.pk).exists()

    # when
    call_command("clearorders")

    # then
    assert not Allocation.objects.exists()


@pytest.mark.django_db
def test_clearorders_removes_gift_cards(gift_card, gift_card_event):
    # given
    assert GiftCard.objects.filter(pk=gift_card.pk).exists()
    assert GiftCardEvent.objects.filter(pk=gift_card_event.pk).exists()

    # when
    call_command("clearorders")

    # then
    assert not GiftCard.objects.exists()
    assert not GiftCardEvent.objects.exists()


@pytest.mark.django_db
def test_clearorders_preserves_catalog(product):
    # given
    product_pk = product.pk

    # when
    call_command("clearorders")

    # then
    assert Product.objects.filter(pk=product_pk).exists()


@pytest.mark.django_db
def test_clearorders_preserves_customers_by_default(customer_user):
    # given
    customer_pk = customer_user.pk

    # when
    call_command("clearorders")

    # then
    assert User.objects.filter(pk=customer_pk).exists()


@pytest.mark.django_db
def test_clearorders_delete_customers_flag_removes_customers(customer_user, staff_user):
    # given
    customer_pk = customer_user.pk
    staff_pk = staff_user.pk

    # when
    call_command("clearorders", delete_customers=True)

    # then
    assert not User.objects.filter(pk=customer_pk).exists()
    assert User.objects.filter(pk=staff_pk).exists()
