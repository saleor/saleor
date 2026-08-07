import pytest
from django.core.management import call_command
from django.test import override_settings

from ....account.models import User
from ....attribute.models import Attribute
from ....checkout.models import Checkout, CheckoutDelivery
from ....discount.models import Promotion, Voucher
from ....giftcard.models import GiftCard
from ....order.models import Order, OrderLine
from ....page.models import Page, PageType
from ....payment.models import Payment, TransactionItem
from ....product.models import Category, Product, ProductType
from ....shipping.models import ShippingMethod, ShippingZone
from ....warehouse.models import Warehouse
from ....webhook.models import Webhook


@override_settings(DEBUG=True)
@pytest.mark.parametrize(
    ("_case", "assign_delivery"),
    [
        ("delivery_not_assigned", False),
        ("delivery_assigned_to_checkout", True),
    ],
)
def test_cleardb_deletes_checkouts_with_checkout_delivery(
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
    call_command("cleardb")

    # then
    assert not Checkout.objects.filter(pk=checkout.pk).exists()
    assert not CheckoutDelivery.objects.filter(pk=delivery.pk).exists()


@override_settings(DEBUG=True)
def test_cleardb_removes_orders_with_lines_payments_and_transactions(
    order_with_lines, payment_dummy, transaction_item
):
    # given
    assert Order.objects.filter(pk=order_with_lines.pk).exists()
    assert OrderLine.objects.filter(order_id=order_with_lines.pk).exists()
    assert Payment.objects.filter(pk=payment_dummy.pk).exists()
    assert TransactionItem.objects.filter(pk=transaction_item.pk).exists()

    # when
    call_command("cleardb")

    # then
    assert not Order.objects.exists()
    assert not OrderLine.objects.exists()
    assert not Payment.objects.exists()
    assert not TransactionItem.objects.exists()


@override_settings(DEBUG=True)
def test_cleardb_removes_catalog_related_objects(
    product, voucher, gift_card, page, warehouse, shipping_zone
):
    # given
    assert Product.objects.exists()
    assert ProductType.objects.exists()
    assert Category.objects.exists()
    assert Attribute.objects.exists()
    assert Voucher.objects.exists()
    assert GiftCard.objects.exists()
    assert Page.objects.exists()
    assert PageType.objects.exists()
    assert Warehouse.objects.exists()
    assert ShippingZone.objects.exists()
    assert ShippingMethod.objects.exists()

    # when
    call_command("cleardb")

    # then
    assert not Product.objects.exists()
    assert not ProductType.objects.exists()
    assert not Category.objects.exists()
    assert not Attribute.objects.exists()
    assert not Voucher.objects.exists()
    assert not GiftCard.objects.exists()
    assert not Page.objects.exists()
    assert not PageType.objects.exists()
    assert not Warehouse.objects.exists()
    assert not ShippingZone.objects.exists()
    assert not ShippingMethod.objects.exists()
    assert not Promotion.objects.exists()


@override_settings(DEBUG=True)
def test_cleardb_removes_webhooks(app, permission_manage_orders):
    # given
    app.permissions.add(permission_manage_orders)
    webhook = Webhook.objects.create(
        name="Test webhook",
        app=app,
        target_url="https://example.com/webhook/",
    )

    # when
    call_command("cleardb")

    # then
    assert not Webhook.objects.filter(pk=webhook.pk).exists()
    app.refresh_from_db()


@override_settings(DEBUG=True)
def test_cleardb_preserves_shop_configuration(
    admin_user, app, site_settings, staff_user, channel_USD, address
):
    # given
    staff_user.addresses.add(address)
    assert staff_user.addresses.count() == 1

    # when
    call_command("cleardb")

    # then
    admin_user.refresh_from_db()
    app.refresh_from_db()
    site_settings.refresh_from_db()
    staff_user.refresh_from_db()
    channel_USD.refresh_from_db()
    assert staff_user.addresses.count() == 0


@override_settings(DEBUG=True)
def test_cleardb_removes_customers_but_keeps_staff(customer_user, staff_user):
    # given
    customer_pk = customer_user.pk
    staff_pk = staff_user.pk

    # when
    call_command("cleardb")

    # then
    assert not User.objects.filter(pk=customer_pk).exists()
    assert User.objects.filter(pk=staff_pk).exists()


@override_settings(DEBUG=True)
def test_cleardb_delete_staff_removes_staff_but_keeps_superuser(staff_user, admin_user):
    # given
    staff_pk = staff_user.pk
    admin_pk = admin_user.pk

    # when
    call_command("cleardb", delete_staff=True)

    # then
    assert not User.objects.filter(pk=staff_pk).exists()
    assert User.objects.filter(pk=admin_pk, is_superuser=True).exists()
