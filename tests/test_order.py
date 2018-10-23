from decimal import Decimal

import pytest
from django.urls import reverse
from django_countries.fields import Country
from payments import FraudStatus, PaymentStatus
from prices import Money, TaxedMoney
from tests.utils import get_redirect_location

from saleor.account.models import User
from saleor.checkout.utils import create_order
from saleor.core.exceptions import InsufficientStock
from saleor.core.utils.taxes import (
    DEFAULT_TAX_RATE_NAME, get_tax_rate_by_name, get_taxes_for_country)
from saleor.order import FulfillmentStatus, OrderStatus, models
from saleor.order.models import Order, Payment
from saleor.order.utils import (
    add_variant_to_order, cancel_fulfillment, cancel_order, recalculate_order,
    restock_fulfillment_lines, restock_order_lines, update_order_prices,
    update_order_status)


def test_total_setter():
    price = TaxedMoney(net=Money(10, 'USD'), gross=Money(15, 'USD'))
    order = models.Order()
    order.total = price
    assert order.total_net == Money(10, 'USD')
    assert order.total.net == Money(10, 'USD')
    assert order.total_gross == Money(15, 'USD')
    assert order.total.gross == Money(15, 'USD')
    assert order.total.tax == Money(5, 'USD')


def test_order_get_subtotal(order_with_lines):
    order_with_lines.discount_name = "Test discount"
    order_with_lines.discount_amount = (
        order_with_lines.total.gross * Decimal('0.5'))
    recalculate_order(order_with_lines)

    target_subtotal = order_with_lines.total - order_with_lines.shipping_price
    target_subtotal += order_with_lines.discount_amount
    assert order_with_lines.get_subtotal() == target_subtotal


def test_get_tax_rate_by_name(taxes):
    rate_name = 'pharmaceuticals'
    tax_rate = get_tax_rate_by_name(rate_name, taxes)

    assert tax_rate == taxes[rate_name]['value']


def test_get_tax_rate_by_name_fallback_to_standard(taxes):
    rate_name = 'unexisting tax rate'
    tax_rate = get_tax_rate_by_name(rate_name, taxes)

    assert tax_rate == taxes[DEFAULT_TAX_RATE_NAME]['value']


def test_get_tax_rate_by_name_empty_taxes(product):
    rate_name = 'unexisting tax rate'
    tax_rate = get_tax_rate_by_name(rate_name)

    assert tax_rate == 0


def test_add_variant_to_order_adds_line_for_new_variant(
        order_with_lines, product, taxes, product_translation_fr, settings):
    order = order_with_lines
    variant = product.variants.get()
    lines_before = order.lines.count()
    settings.LANGUAGE_CODE = 'fr'
    add_variant_to_order(order, variant, 1, taxes=taxes)

    line = order.lines.last()
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.quantity == 1
    assert line.unit_price == TaxedMoney(
        net=Money('8.13', 'USD'), gross=Money(10, 'USD'))
    assert line.tax_rate == taxes[product.tax_rate]['value']
    assert line.translated_product_name == variant.display_product(
        translated=True)


@pytest.mark.parametrize('track_inventory', (True, False))
def test_add_variant_to_order_allocates_stock_for_new_variant(
        order_with_lines, product, track_inventory):
    variant = product.variants.get()
    variant.track_inventory = track_inventory
    variant.save()

    stock_before = variant.quantity_allocated

    add_variant_to_order(order_with_lines, variant, 1)

    variant.refresh_from_db()
    if track_inventory:
        assert variant.quantity_allocated == stock_before + 1
    else:
        assert variant.quantity_allocated == stock_before


def test_add_variant_to_order_edits_line_for_existing_variant(
        order_with_lines):
    existing_line = order_with_lines.lines.first()
    variant = existing_line.variant
    lines_before = order_with_lines.lines.count()
    line_quantity_before = existing_line.quantity

    add_variant_to_order(order_with_lines, variant, 1)

    existing_line.refresh_from_db()
    assert order_with_lines.lines.count() == lines_before
    assert existing_line.product_sku == variant.sku
    assert existing_line.quantity == line_quantity_before + 1


def test_add_variant_to_order_allocates_stock_for_existing_variant(
        order_with_lines):
    existing_line = order_with_lines.lines.first()
    variant = existing_line.variant
    stock_before = variant.quantity_allocated

    add_variant_to_order(order_with_lines, variant, 1)

    variant.refresh_from_db()
    assert variant.quantity_allocated == stock_before + 1


def test_add_variant_to_order_allow_overselling(order_with_lines):
    existing_line = order_with_lines.lines.first()
    variant = existing_line.variant
    stock_before = variant.quantity_allocated

    quantity = variant.quantity + 1
    with pytest.raises(InsufficientStock):
        add_variant_to_order(
            order_with_lines, variant, quantity, allow_overselling=False)

    add_variant_to_order(
        order_with_lines, variant, quantity, allow_overselling=True)
    variant.refresh_from_db()
    assert variant.quantity_allocated == stock_before + quantity


def test_view_connect_order_with_user_authorized_user(
        order, authorized_client, customer_user):
    order.user_email = customer_user.email
    order.save()

    url = reverse(
        'order:connect-order-with-user', kwargs={'token': order.token})
    response = authorized_client.post(url)

    redirect_location = get_redirect_location(response)
    assert redirect_location == reverse('order:details', args=[order.token])
    order.refresh_from_db()
    assert order.user == customer_user


def test_view_connect_order_with_user_different_email(
        order, authorized_client, customer_user):
    """Order was placed from different email, than user's
    we are trying to assign it to."""
    order.user = None
    order.user_email = 'example_email@email.email'
    order.save()

    assert order.user_email != customer_user.email

    url = reverse(
        'order:connect-order-with-user', kwargs={'token': order.token})
    response = authorized_client.post(url)

    redirect_location = get_redirect_location(response)
    assert redirect_location == reverse('account:details')
    order.refresh_from_db()
    assert order.user is None


def test_view_order_with_deleted_variant(authorized_client, order_with_lines):
    order = order_with_lines
    order_details_url = reverse('order:details', kwargs={'token': order.token})

    # delete a variant associated to the order
    order.lines.first().variant.delete()

    # check if the order details view handles the deleted variant
    response = authorized_client.get(order_details_url)
    assert response.status_code == 200


def test_view_fulfilled_order_with_deleted_variant(
        authorized_client, fulfilled_order):
    order = fulfilled_order
    order_details_url = reverse('order:details', kwargs={'token': order.token})

    # delete a variant associated to the order
    order.lines.first().variant.delete()

    # check if the order details view handles the deleted variant
    response = authorized_client.get(order_details_url)
    assert response.status_code == 200


@pytest.mark.parametrize('track_inventory', (True, False))
def test_restock_order_lines(order_with_lines, track_inventory):

    order = order_with_lines
    line_1 = order.lines.first()
    line_2 = order.lines.last()

    line_1.variant.track_inventory = track_inventory
    line_2.variant.track_inventory = track_inventory

    line_1.variant.save()
    line_2.variant.save()

    stock_1_quantity_allocated_before = line_1.variant.quantity_allocated
    stock_2_quantity_allocated_before = line_2.variant.quantity_allocated

    stock_1_quantity_before = line_1.variant.quantity
    stock_2_quantity_before = line_2.variant.quantity

    restock_order_lines(order)

    line_1.variant.refresh_from_db()
    line_2.variant.refresh_from_db()

    if track_inventory:
        assert line_1.variant.quantity_allocated == (
            stock_1_quantity_allocated_before - line_1.quantity)
        assert line_2.variant.quantity_allocated == (
            stock_2_quantity_allocated_before - line_2.quantity)
    else:
        assert line_1.variant.quantity_allocated == (
            stock_1_quantity_allocated_before)
        assert line_2.variant.quantity_allocated == (
            stock_2_quantity_allocated_before)

    assert line_1.variant.quantity == stock_1_quantity_before
    assert line_2.variant.quantity == stock_2_quantity_before
    assert line_1.quantity_fulfilled == 0
    assert line_2.quantity_fulfilled == 0


def test_restock_fulfilled_order_lines(fulfilled_order):
    line_1 = fulfilled_order.lines.first()
    line_2 = fulfilled_order.lines.last()
    stock_1_quantity_allocated_before = line_1.variant.quantity_allocated
    stock_2_quantity_allocated_before = line_2.variant.quantity_allocated
    stock_1_quantity_before = line_1.variant.quantity
    stock_2_quantity_before = line_2.variant.quantity

    restock_order_lines(fulfilled_order)

    line_1.variant.refresh_from_db()
    line_2.variant.refresh_from_db()
    assert line_1.variant.quantity_allocated == (
        stock_1_quantity_allocated_before)
    assert line_2.variant.quantity_allocated == (
        stock_2_quantity_allocated_before)
    assert line_1.variant.quantity == stock_1_quantity_before + line_1.quantity
    assert line_2.variant.quantity == stock_2_quantity_before + line_2.quantity


def test_restock_fulfillment_lines(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    line_1 = fulfillment.lines.first()
    line_2 = fulfillment.lines.last()
    stock_1 = line_1.order_line.variant
    stock_2 = line_2.order_line.variant
    stock_1_quantity_allocated_before = stock_1.quantity_allocated
    stock_2_quantity_allocated_before = stock_2.quantity_allocated
    stock_1_quantity_before = stock_1.quantity
    stock_2_quantity_before = stock_2.quantity

    restock_fulfillment_lines(fulfillment)

    stock_1.refresh_from_db()
    stock_2.refresh_from_db()
    assert stock_1.quantity_allocated == (
        stock_1_quantity_allocated_before + line_1.quantity)
    assert stock_2.quantity_allocated == (
        stock_2_quantity_allocated_before + line_2.quantity)
    assert stock_1.quantity == stock_1_quantity_before + line_1.quantity
    assert stock_2.quantity == stock_2_quantity_before + line_2.quantity


def test_cancel_order(fulfilled_order):
    cancel_order(fulfilled_order, restock=False)
    assert all([
        f.status == FulfillmentStatus.CANCELED
        for f in fulfilled_order.fulfillments.all()])
    assert fulfilled_order.status == OrderStatus.CANCELED


def test_cancel_fulfillment(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    line_1 = fulfillment.lines.first()
    line_2 = fulfillment.lines.first()

    cancel_fulfillment(fulfillment, restock=False)

    assert fulfillment.status == FulfillmentStatus.CANCELED
    assert fulfilled_order.status == OrderStatus.UNFULFILLED
    assert line_1.order_line.quantity_fulfilled == 0
    assert line_2.order_line.quantity_fulfilled == 0


def test_update_order_status(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    line = fulfillment.lines.first()
    order_line = line.order_line

    order_line.quantity_fulfilled -= line.quantity
    order_line.save()
    line.delete()
    update_order_status(fulfilled_order)

    assert fulfilled_order.status == OrderStatus.PARTIALLY_FULFILLED

    line = fulfillment.lines.first()
    order_line = line.order_line

    order_line.quantity_fulfilled -= line.quantity
    order_line.save()
    line.delete()
    update_order_status(fulfilled_order)

    assert fulfilled_order.status == OrderStatus.UNFULFILLED


def test_order_queryset_confirmed(draft_order):
    other_orders = [
        Order.objects.create(status=OrderStatus.UNFULFILLED),
        Order.objects.create(status=OrderStatus.PARTIALLY_FULFILLED),
        Order.objects.create(status=OrderStatus.FULFILLED),
        Order.objects.create(status=OrderStatus.CANCELED)]

    confirmed_orders = Order.objects.confirmed()

    assert draft_order not in confirmed_orders
    assert all([order in confirmed_orders for order in other_orders])


def test_order_queryset_drafts(draft_order):
    other_orders = [
        Order.objects.create(status=OrderStatus.UNFULFILLED),
        Order.objects.create(status=OrderStatus.PARTIALLY_FULFILLED),
        Order.objects.create(status=OrderStatus.FULFILLED),
        Order.objects.create(status=OrderStatus.CANCELED)
    ]

    draft_orders = Order.objects.drafts()

    assert draft_order in draft_orders
    assert all([order not in draft_orders for order in other_orders])


def test_order_queryset_to_ship():
    total = TaxedMoney(net=Money(10, 'USD'), gross=Money(15, 'USD'))
    orders_to_ship = [
        Order.objects.create(status=OrderStatus.UNFULFILLED, total=total),
        Order.objects.create(
            status=OrderStatus.PARTIALLY_FULFILLED, total=total)
    ]
    for order in orders_to_ship:
        order.payments.create(
            variant='default', status=PaymentStatus.CONFIRMED, currency='USD',
            total=order.total_gross.amount,
            captured_amount=order.total_gross.amount)

    orders_not_to_ship = [
        Order.objects.create(status=OrderStatus.DRAFT, total=total),
        Order.objects.create(status=OrderStatus.UNFULFILLED, total=total),
        Order.objects.create(
            status=OrderStatus.PARTIALLY_FULFILLED, total=total),
        Order.objects.create(status=OrderStatus.FULFILLED, total=total),
        Order.objects.create(status=OrderStatus.CANCELED, total=total)
    ]

    orders = Order.objects.ready_to_fulfill()

    assert all([order in orders for order in orders_to_ship])
    assert all([order not in orders for order in orders_not_to_ship])


def test_queryset_ready_to_capture():
    total = TaxedMoney(net=Money(10, 'USD'), gross=Money(15, 'USD'))

    preauth_order = Order.objects.create(
        status=OrderStatus.UNFULFILLED, total=total)
    Payment.objects.create(order=preauth_order, status=PaymentStatus.PREAUTH)

    orders = [
        Order.objects.create(status=OrderStatus.DRAFT, total=total),
        Order.objects.create(status=OrderStatus.UNFULFILLED, total=total),
        preauth_order,
        Order.objects.create(status=OrderStatus.CANCELED, total=total)]

    qs = Order.objects.ready_to_capture()
    assert preauth_order in qs
    statuses = [o.status for o in qs]
    assert OrderStatus.DRAFT not in statuses
    assert OrderStatus.CANCELED not in statuses


def test_update_order_prices(order_with_lines):
    taxes = get_taxes_for_country(Country('DE'))
    address = order_with_lines.shipping_address
    address.country = 'DE'
    address.save()

    line_1 = order_with_lines.lines.first()
    line_2 = order_with_lines.lines.last()
    price_1 = line_1.variant.get_price(taxes=taxes)
    price_2 = line_2.variant.get_price(taxes=taxes)
    shipping_price = order_with_lines.shipping_method.get_total(taxes)

    update_order_prices(order_with_lines, None)

    line_1.refresh_from_db()
    line_2.refresh_from_db()
    assert line_1.unit_price == price_1
    assert line_2.unit_price == price_2
    assert order_with_lines.shipping_price == shipping_price
    total = (
        line_1.quantity * price_1 + line_2.quantity * price_2 + shipping_price)
    assert order_with_lines.total == total


def test_order_payment_flow(
        request_cart_with_item, client, address, shipping_zone):
    request_cart_with_item.shipping_address = address
    request_cart_with_item.billing_address = address.get_copy()
    request_cart_with_item.email = 'test@example.com'
    request_cart_with_item.shipping_method = (
        shipping_zone.shipping_methods.first())
    request_cart_with_item.save()

    order = create_order(
        request_cart_with_item, 'tracking_code', discounts=None, taxes=None)

    # Select payment method
    url = reverse('order:payment', kwargs={'token': order.token})
    data = {'method': 'default'}
    response = client.post(url, data, follow=True)

    assert len(response.redirect_chain) == 1
    assert response.status_code == 200
    redirect_url = reverse(
        'order:payment', kwargs={'token': order.token, 'variant': 'default'})
    assert response.request['PATH_INFO'] == redirect_url

    # Go to payment details page, enter payment data
    data = {
        'status': PaymentStatus.PREAUTH,
        'fraud_status': FraudStatus.UNKNOWN,
        'gateway_response': '3ds-disabled',
        'verification_result': 'waiting'}

    response = client.post(redirect_url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'order:payment-success', kwargs={'token': order.token})
    assert get_redirect_location(response) == redirect_url

    # Complete payment, go to checkout success page
    data = {'status': 'ok'}
    response = client.post(redirect_url, data)
    assert response.status_code == 302
    redirect_url = reverse(
        'order:checkout-success', kwargs={'token': order.token})
    assert get_redirect_location(response) == redirect_url

    # Assert that payment object was created and contains correct data
    payment = order.payments.all()[0]
    assert payment.total == order.total.gross.amount
    assert payment.tax == order.total.tax.amount
    assert payment.currency == order.total.currency
    assert payment.delivery == order.shipping_price.net.amount
    assert len(payment.get_purchased_items()) == len(order.lines.all())


def test_create_user_after_order(order, client):
    order.user_email = 'hello@mirumee.com'
    order.save()
    url = reverse('order:checkout-success', kwargs={'token': order.token})
    data = {'password': 'password'}

    response = client.post(url, data)

    redirect_url = reverse('order:details', kwargs={'token': order.token})
    assert get_redirect_location(response) == redirect_url
    user = User.objects.filter(email='hello@mirumee.com').first()
    assert user is not None
    assert user.orders.filter(token=order.token).exists()


def test_view_order_details(order, client):
    url = reverse('order:details', kwargs={'token': order.token})
    response = client.get(url)
    assert response.status_code == 200


def test_add_order_note_view(order, authorized_client, customer_user):
    order.user_email = customer_user.email
    order.save()
    url = reverse('order:details', kwargs={'token': order.token})
    customer_note = 'bla-bla note'
    data = {'customer_note': customer_note}

    response = authorized_client.post(url, data)

    redirect_url = reverse('order:details', kwargs={'token': order.token})
    assert get_redirect_location(response) == redirect_url
    order.refresh_from_db()
    assert order.customer_note == customer_note
