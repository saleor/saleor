import json
from decimal import Decimal

from django.urls import reverse
from payments import PaymentStatus
from prices import Money, TaxedMoney
from tests.utils import get_redirect_location

from saleor.order import FulfillmentStatus, OrderStatus, models
from saleor.order.forms import OrderNoteForm
from saleor.order.models import Order
from saleor.order.utils import (
    add_variant_to_order, cancel_fulfillment, cancel_order, recalculate_order,
    restock_fulfillment_lines, restock_order_lines, update_order_status)


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


def test_add_variant_to_order_adds_line_for_new_variant(
        order_with_lines, product_in_stock):
    order = order_with_lines
    variant = product_in_stock.variants.get()
    lines_before = order.lines.count()

    add_variant_to_order(order, variant, 1)

    line = order.lines.last()
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.quantity == 1


def test_add_variant_to_order_allocates_stock_for_new_variant(
        order_with_lines, product_in_stock):
    order = order_with_lines
    variant = product_in_stock.variants.get()
    stock = variant.select_stockrecord()
    stock_before = stock.quantity_allocated

    add_variant_to_order(order, variant, 1)

    stock.refresh_from_db()
    assert stock.quantity_allocated == stock_before + 1


def test_add_variant_to_order_edits_line_for_existing_variant(
        order_with_lines):
    order = order_with_lines
    existing_line = order.lines.first()
    variant = existing_line.product.variants.get()
    lines_before = order.lines.count()
    line_quantity_before = existing_line.quantity

    add_variant_to_order(order, variant, 1)

    existing_line.refresh_from_db()
    assert order.lines.count() == lines_before
    assert existing_line.product_sku == variant.sku
    assert existing_line.quantity == line_quantity_before + 1


def test_add_variant_to_order_allocates_stock_for_existing_variant(
        order_with_lines):
    order = order_with_lines
    existing_line = order.lines.first()
    variant = existing_line.product.variants.get()
    stock = existing_line.stock
    stock_before = stock.quantity_allocated

    add_variant_to_order(order, variant, 1)

    stock.refresh_from_db()
    assert stock.quantity_allocated == stock_before + 1


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


def test_add_note_to_order(order_with_lines):
    order = order_with_lines
    note = models.OrderNote(order=order, user=order.user)
    note_form = OrderNoteForm({'content': 'test_note'}, instance=note)
    note_form.is_valid()
    note_form.save()
    assert order.notes.first().content == 'test_note'


def test_create_order_history(order_with_lines):
    order = order_with_lines
    order.history.create(content='test_entry', user=order.user)
    history_entry = models.OrderHistoryEntry.objects.get(order=order)
    assert history_entry == order.history.first()
    assert history_entry.content == 'test_entry'


def test_restock_order_lines(order_with_lines):
    order = order_with_lines
    line_1 = order.lines.first()
    line_2 = order.lines.last()
    stock_1_quantity_allocated_before = line_1.stock.quantity_allocated
    stock_2_quantity_allocated_before = line_2.stock.quantity_allocated
    stock_1_quantity_before = line_1.stock.quantity
    stock_2_quantity_before = line_2.stock.quantity

    restock_order_lines(order)

    line_1.stock.refresh_from_db()
    line_2.stock.refresh_from_db()
    assert line_1.stock.quantity_allocated == (
        stock_1_quantity_allocated_before - line_1.quantity)
    assert line_2.stock.quantity_allocated == (
        stock_2_quantity_allocated_before - line_2.quantity)
    assert line_1.stock.quantity == stock_1_quantity_before
    assert line_2.stock.quantity == stock_2_quantity_before
    assert line_1.quantity_fulfilled == 0
    assert line_2.quantity_fulfilled == 0


def test_restock_fulfilled_order_lines(fulfilled_order):
    line_1 = fulfilled_order.lines.first()
    line_2 = fulfilled_order.lines.last()
    stock_1_quantity_allocated_before = line_1.stock.quantity_allocated
    stock_2_quantity_allocated_before = line_2.stock.quantity_allocated
    stock_1_quantity_before = line_1.stock.quantity
    stock_2_quantity_before = line_2.stock.quantity

    restock_order_lines(fulfilled_order)

    line_1.stock.refresh_from_db()
    line_2.stock.refresh_from_db()
    assert line_1.stock.quantity_allocated == (
        stock_1_quantity_allocated_before)
    assert line_2.stock.quantity_allocated == (
        stock_2_quantity_allocated_before)
    assert line_1.stock.quantity == stock_1_quantity_before + line_1.quantity
    assert line_2.stock.quantity == stock_2_quantity_before + line_2.quantity


def test_restock_fulfillment_lines(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    line_1 = fulfillment.lines.first()
    line_2 = fulfillment.lines.last()
    stock_1 = line_1.order_line.stock
    stock_2 = line_2.order_line.stock
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
        Order.objects.create(status=OrderStatus.CANCELED)
    ]

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

    orders = Order.objects.to_ship()

    assert all([order in orders for order in orders_to_ship])
    assert all([order not in orders for order in orders_not_to_ship])


def test_ajax_order_shipping_methods_list(
        admin_client, order, shipping_method):
    method = shipping_method.price_per_country.get()
    shipping_methods_list = [{'id': method.pk, 'text': method.ajax_label}]
    url = reverse(
        'dashboard:ajax-order-shipping-methods', kwargs={'order_pk': order.pk})

    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    resp_decoded = json.loads(response.content.decode('utf-8'))

    assert response.status_code == 200
    assert resp_decoded == {'results': shipping_methods_list}


def test_ajax_order_shipping_methods_list_different_country(
        admin_client, order, shipping_method):
    order.shipping_address = order.billing_address.get_copy()
    order.save()
    method = shipping_method.price_per_country.get()
    shipping_methods_list = [{'id': method.pk, 'text': method.ajax_label}]
    shipping_method.price_per_country.create(price=15, country_code='DE')
    url = reverse(
        'dashboard:ajax-order-shipping-methods', kwargs={'order_pk': order.pk})

    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    resp_decoded = json.loads(response.content.decode('utf-8'))

    assert response.status_code == 200
    assert resp_decoded == {'results': shipping_methods_list}
