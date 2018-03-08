from decimal import Decimal
from unittest.mock import Mock

from django.urls import reverse
from prices import Money, TaxedMoney
from tests.utils import get_redirect_location

from saleor.order import FulfillmentStatus, models, OrderStatus
from saleor.order.emails import collect_data_for_email
from saleor.order.forms import OrderNoteForm
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
        order_with_lines_and_stock):
    order = order_with_lines_and_stock
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
        order_with_lines_and_stock):
    order = order_with_lines_and_stock
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
        order, authorized_client):
    url = reverse(
        'order:connect-order-with-user', kwargs={'token': order.token})
    response = authorized_client.post(url)

    redirect_location = get_redirect_location(response)
    assert redirect_location == reverse('account:details')
    order.refresh_from_db()
    assert order.user is None


def test_add_note_to_order(order_with_lines_and_stock):
    order = order_with_lines_and_stock
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


def test_collect_data_for_email(order):
    template = Mock(spec=str)
    order.user_mail = 'test@example.com'
    email_data = collect_data_for_email(order.pk, template)
    order_url = reverse('order:details', kwargs={'token': order.token})
    assert order_url in email_data['url']
    assert email_data['email'] == order.user_email


def test_restock_order_lines(order_with_lines_and_stock):
    order = order_with_lines_and_stock
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
    assert stock_1.quantity_allocated == stock_1_quantity_allocated_before
    assert stock_1.quantity_allocated == stock_2_quantity_allocated_before
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
    cancel_fulfillment(fulfillment, restock=False)
    assert fulfillment.status == FulfillmentStatus.CANCELED
    assert fulfilled_order.status == OrderStatus.UNFULFILLED


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
