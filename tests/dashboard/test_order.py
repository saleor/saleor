from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from payments import FraudStatus, PaymentStatus
from prices import Money, TaxedMoney
from tests.utils import get_redirect_location, get_url_path

from saleor.dashboard.order.forms import ChangeQuantityForm, OrderNoteForm
from saleor.dashboard.order.utils import fulfill_order_line
from saleor.order.models import Order, OrderHistoryEntry, OrderLine, OrderNote
from saleor.order.utils import (
    add_variant_to_existing_lines, add_variant_to_order,
    change_order_line_quantity)
from saleor.product.models import ProductVariant, Stock, StockLocation


@pytest.mark.integration
@pytest.mark.django_db
def test_view_capture_order_payment(admin_client, order_with_lines_and_stock):
    order = order_with_lines_and_stock
    payment = order.payments.create(
        variant='default', status=PaymentStatus.PREAUTH,
        fraud_status=FraudStatus.ACCEPT, currency='USD', total='100.0')

    url = reverse(
        'dashboard:capture-payment', kwargs={
            'order_pk': order.pk,
            'payment_pk': payment.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 302
    assert order.payments.last().get_captured_price() == TaxedMoney(
        net=Money(20, 'USD'), gross=Money(20, 'USD'))


@pytest.mark.integration
@pytest.mark.django_db
def test_view_refund_order_payment(admin_client, order_with_lines_and_stock):
    order = order_with_lines_and_stock
    payment = order.payments.create(
        variant='default', status=PaymentStatus.CONFIRMED,
        fraud_status=FraudStatus.ACCEPT, currency='USD', total='100.0',
        captured_amount='100.0')

    url = reverse(
        'dashboard:refund-payment', kwargs={
            'order_pk': order.pk,
            'payment_pk': payment.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 302
    assert order.payments.last().get_captured_price() == TaxedMoney(
        net=Money(80, 'USD'), gross=Money(80, 'USD'))


@pytest.mark.integration
@pytest.mark.django_db
def test_view_cancel_order_line(admin_client, order_with_lines_and_stock):
    lines_before = order_with_lines_and_stock.lines.all()
    lines_before_count = lines_before.count()
    line = lines_before.first()
    line_quantity = line.quantity
    quantity_allocated_before = line.stock.quantity_allocated
    product = line.product

    url = reverse(
        'dashboard:orderline-cancel', kwargs={
            'order_pk': order_with_lines_and_stock.pk,
            'line_pk': line.pk})

    response = admin_client.get(url)
    assert response.status_code == 200
    response = admin_client.post(url, {'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse(
        'dashboard:order-details', args=[order_with_lines_and_stock.pk])
    # check ordered item removal
    lines_after = Order.objects.get().lines.all()
    assert lines_before_count - 1 == lines_after.count()
    # check stock deallocation
    assert Stock.objects.first().quantity_allocated == (
        quantity_allocated_before - line_quantity)
    # check note in the order's history
    assert OrderHistoryEntry.objects.get(
        order=order_with_lines_and_stock).content == (
            'Cancelled item %s' % product)
    url = reverse(
        'dashboard:orderline-cancel', kwargs={
            'order_pk': order_with_lines_and_stock.pk,
            'line_pk': OrderLine.objects.get().pk})
    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello'}, follow=True)
    assert Order.objects.get().lines.all().count() == 0
    # check success messages after redirect
    assert response.context['messages']


@pytest.mark.integration
@pytest.mark.django_db
def test_view_change_order_line_quantity(
        admin_client, order_with_lines_and_stock):
    lines_before_quantity_change = order_with_lines_and_stock.lines.all()
    lines_before_quantity_change_count = lines_before_quantity_change.count()
    line = lines_before_quantity_change.first()
    line_quantity_before_quantity_change = line.quantity

    url = reverse(
        'dashboard:orderline-change-quantity', kwargs={
            'order_pk': order_with_lines_and_stock.pk,
            'line_pk': line.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    response = admin_client.post(
        url, {'quantity': 2}, follow=True)
    redirected_to, redirect_status_code = response.redirect_chain[-1]
    # check redirection
    assert redirect_status_code == 302
    assert get_url_path(redirected_to) == reverse(
        'dashboard:order-details',
        args=[order_with_lines_and_stock.pk])
    # success messages should appear after redirect
    assert response.context['messages']
    lines_after = Order.objects.get().lines.all()
    # order should have the same lines
    assert lines_before_quantity_change_count == lines_after.count()
    # stock allocation should be 2 now
    assert Stock.objects.first().quantity_allocated == 2
    line.refresh_from_db()
    # source line quantity should be decreased to 2
    assert line.quantity == 2
    # a note in the order's history should be created
    assert OrderHistoryEntry.objects.get(
        order=order_with_lines_and_stock).content == (
            'Changed quantity for product %(product)s from'
            ' %(old_quantity)s to %(new_quantity)s') % {
                'product': line.product,
                'old_quantity': line_quantity_before_quantity_change,
                'new_quantity': 2}


@pytest.mark.integration
@pytest.mark.django_db
def test_view_change_order_line_quantity_with_invalid_data(
        admin_client, order_with_lines_and_stock):
    lines = order_with_lines_and_stock.lines.all()
    line = lines.first()
    url = reverse(
        'dashboard:orderline-change-quantity', kwargs={
            'order_pk': order_with_lines_and_stock.pk,
            'line_pk': line.pk})
    response = admin_client.post(
        url, {'quantity': 0})
    assert response.status_code == 400


def test_dashboard_change_quantity_form(request_cart_with_item, order):
    cart = request_cart_with_item
    for line in cart.lines.all():
        add_variant_to_order(order, line.variant, line.quantity)
    order_line = order.lines.get()

    # Check max quantity validation
    form = ChangeQuantityForm({'quantity': 9999}, instance=order_line)
    assert not form.is_valid()
    assert form.errors['quantity'] == [
        'Ensure this value is less than or equal to 50.']

    # Check minimum quantity validation
    form = ChangeQuantityForm({'quantity': 0}, instance=order_line)
    assert not form.is_valid()
    assert order.lines.get().stock.quantity_allocated == 1

    # Check available quantity validation
    form = ChangeQuantityForm({'quantity': 20}, instance=order_line)
    assert not form.is_valid()
    assert order.lines.get().stock.quantity_allocated == 1
    assert form.errors['quantity'] == ['Only 5 remaining in stock.']

    # Save same quantity
    form = ChangeQuantityForm({'quantity': 1}, instance=order_line)
    assert form.is_valid()
    form.save()
    order_line.stock.refresh_from_db()
    assert order.lines.get().stock.quantity_allocated == 1

    # Increase quantity
    form = ChangeQuantityForm({'quantity': 2}, instance=order_line)
    assert form.is_valid()
    form.save()
    order_line.stock.refresh_from_db()
    assert order.lines.get().stock.quantity_allocated == 2

    # Decrease quantity
    form = ChangeQuantityForm({'quantity': 1}, instance=order_line)
    assert form.is_valid()
    form.save()
    assert order.lines.get().stock.quantity_allocated == 1


def test_ordered_item_change_quantity(transactional_db, order_with_lines):
    assert list(order_with_lines.history.all()) == []
    lines = order_with_lines.lines.all()
    change_order_line_quantity(lines[2], 0)
    change_order_line_quantity(lines[1], 0)
    change_order_line_quantity(lines[0], 0)
    assert order_with_lines.get_total_quantity() == 0


@pytest.mark.integration
@pytest.mark.django_db
def test_view_order_invoice(
        admin_client, order_with_lines_and_stock, billing_address):
    order_with_lines_and_stock.shipping_address = billing_address
    order_with_lines_and_stock.billing_address = billing_address
    order_with_lines_and_stock.save()
    url = reverse(
        'dashboard:order-invoice', kwargs={
            'order_pk': order_with_lines_and_stock.id})
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/pdf'
    name = "invoice-%s" % order_with_lines_and_stock.id
    assert response['Content-Disposition'] == 'filename=%s' % name


@pytest.mark.integration
@pytest.mark.django_db
def test_view_order_invoice_without_shipping(
        admin_client, order_with_lines_and_stock, billing_address):
    # Regression test for #1536:
    order_with_lines_and_stock.billing_address = billing_address
    order_with_lines_and_stock.save()
    url = reverse(
        'dashboard:order-invoice', kwargs={
            'order_pk': order_with_lines_and_stock.id})
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/pdf'


@pytest.mark.integration
@pytest.mark.django_db
def test_view_fulfillment_packing_slips(
        admin_client, fulfilled_order, billing_address):
    fulfilled_order.shipping_address = billing_address
    fulfilled_order.billing_address = billing_address
    fulfilled_order.save()
    fulfillment = fulfilled_order.fulfillments.first()
    url = reverse(
        'dashboard:fulfillment-packing-slips', kwargs={
            'order_pk': fulfilled_order.pk, 'fulfillment_pk': fulfillment.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/pdf'
    name = "packing-slip-%s" % (fulfilled_order.id,)
    assert response['Content-Disposition'] == 'filename=%s' % name


@pytest.mark.integration
@pytest.mark.django_db
def test_view_fulfillment_packing_slips_without_shipping(
        admin_client, fulfilled_order, billing_address):
    # Regression test for #1536
    fulfilled_order.billing_address = billing_address
    fulfilled_order.save()
    fulfillment = fulfilled_order.fulfillments.first()
    url = reverse(
        'dashboard:fulfillment-packing-slips', kwargs={
            'order_pk': fulfilled_order.pk, 'fulfillment_pk': fulfillment.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/pdf'


@pytest.mark.integration
@pytest.mark.django_db
def test_view_change_order_line_stock_valid(
        admin_client, order_with_lines_and_stock):
    order = order_with_lines_and_stock
    line = order.lines.last()
    old_stock = line.stock
    variant = ProductVariant.objects.get(sku=line.product_sku)
    stock_location = StockLocation.objects.create(name='Warehouse 2')
    stock = Stock.objects.create(
        variant=variant, cost_price=2, quantity=2, quantity_allocated=0,
        location=stock_location)

    url = reverse(
        'dashboard:orderline-change-stock', kwargs={
            'order_pk': order.pk,
            'line_pk': line.pk})
    data = {'stock': stock.pk}
    response = admin_client.post(url, data)

    assert response.status_code == 200

    line.refresh_from_db()
    assert line.stock == stock
    assert line.stock_location == stock.location.name
    assert line.stock.quantity_allocated == 2

    old_stock.refresh_from_db()
    assert old_stock.quantity_allocated == 0


@pytest.mark.integration
@pytest.mark.django_db
def test_view_change_order_line_stock_insufficient_stock(
        admin_client, order_with_lines_and_stock):
    order = order_with_lines_and_stock
    line = order.lines.last()
    old_stock = line.stock
    variant = ProductVariant.objects.get(sku=line.product_sku)
    stock_location = StockLocation.objects.create(name='Warehouse 2')
    stock = Stock.objects.create(
        variant=variant, cost_price=2, quantity=2, quantity_allocated=1,
        location=stock_location)

    url = reverse(
        'dashboard:orderline-change-stock', kwargs={
            'order_pk': order.pk,
            'line_pk': line.pk})
    data = {'stock': stock.pk}
    response = admin_client.post(url, data)

    assert response.status_code == 400

    line.refresh_from_db()
    assert line.stock == old_stock
    assert line.stock_location == old_stock.location.name

    old_stock.refresh_from_db()
    assert old_stock.quantity_allocated == 2

    stock.refresh_from_db()
    assert stock.quantity_allocated == 1


def test_view_change_order_line_stock_merges_lines(
        admin_client, order_with_lines_and_stock):
    order = order_with_lines_and_stock
    line = order.lines.first()
    old_stock = line.stock
    variant = ProductVariant.objects.get(sku=line.product_sku)
    stock_location = StockLocation.objects.create(name='Warehouse 2')
    stock = Stock.objects.create(
        variant=variant, cost_price=2, quantity=2, quantity_allocated=2,
        location=stock_location)
    line_2 = order.lines.create(
        product=line.product,
        product_name=line.product.name,
        product_sku='SKU_A',
        is_shipping_required=line.is_shipping_required,
        quantity=2,
        unit_price_net=Decimal('30.00'),
        unit_price_gross=Decimal('30.00'),
        stock=stock,
        stock_location=stock.location.name)
    lines_before = order.lines.count()

    url = reverse(
        'dashboard:orderline-change-stock', kwargs={
            'order_pk': order.pk,
            'line_pk': line_2.pk})
    data = {'stock': old_stock.pk}
    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert order.lines.count() == lines_before - 1

    old_stock.refresh_from_db()
    assert old_stock.quantity_allocated == 5

    stock.refresh_from_db()
    assert stock.quantity_allocated == 0


def test_add_variant_to_existing_lines_one_line(
        order_with_variant_from_different_stocks):
    order = order_with_variant_from_different_stocks
    lines = order.lines.filter(product_sku='SKU_A')
    variant_lines_before = lines.count()
    line = lines.get(stock_location='Warehouse 2')
    variant = ProductVariant.objects.get(sku='SKU_A')

    quantity_left = add_variant_to_existing_lines(line.order, variant, 2)

    lines_after = order.lines.filter(product_sku='SKU_A').count()
    line.refresh_from_db()
    assert quantity_left == 0
    assert lines_after == variant_lines_before
    assert line.quantity == 4


def test_add_variant_to_existing_lines_multiple_lines(
        order_with_variant_from_different_stocks):
    order = order_with_variant_from_different_stocks
    lines = order.lines.filter(product_sku='SKU_A')
    variant_lines_before = lines.count()
    line_1 = lines.get(stock_location='Warehouse 1')
    line_2 = lines.get(stock_location='Warehouse 2')
    variant = ProductVariant.objects.get(sku='SKU_A')

    quantity_left = add_variant_to_existing_lines(line_1.order, variant, 4)

    lines_after = order.lines.filter(product_sku='SKU_A').count()
    line_1.refresh_from_db()
    line_2.refresh_from_db()
    assert quantity_left == 0
    assert lines_after == variant_lines_before
    assert line_1.quantity == 4
    assert line_2.quantity == 5


def test_add_variant_to_existing_lines_multiple_lines_with_rest(
        order_with_variant_from_different_stocks):
    order = order_with_variant_from_different_stocks
    lines = order.lines.filter(product_sku='SKU_A')
    variant_lines_before = lines.count()
    line_1 = lines.get(stock_location='Warehouse 1')
    line_2 = lines.get(stock_location='Warehouse 2')
    variant = ProductVariant.objects.get(sku='SKU_A')

    quantity_left = add_variant_to_existing_lines(line_1.order, variant, 7)

    lines_after = order.lines.filter(product_sku='SKU_A').count()
    line_1.refresh_from_db()
    line_2.refresh_from_db()
    assert quantity_left == 2
    assert lines_after == variant_lines_before
    assert line_1.quantity == 5
    assert line_2.quantity == 5


def test_view_add_variant_to_order(
        admin_client, order_with_variant_from_different_stocks):
    order = order_with_variant_from_different_stocks
    variant = ProductVariant.objects.get(sku='SKU_A')
    line = OrderLine.objects.get(
        product_sku='SKU_A', stock_location='Warehouse 2')
    url = reverse(
        'dashboard:add-variant-to-order', kwargs={'order_pk': order.pk})
    data = {'variant': variant.pk, 'quantity': 2}

    response = admin_client.post(url, data)

    line.refresh_from_db()
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse(
        'dashboard:order-details', kwargs={'order_pk': order.pk})
    assert line.quantity == 4


@patch('saleor.dashboard.order.forms.send_note_confirmation')
def test_note_form_sent_email(
        mock_send_note_confirmation, order_with_lines_and_stock):
    order = order_with_lines_and_stock
    note = OrderNote(order=order, user=order.user)
    form = OrderNoteForm({'content': 'test_note'}, instance=note)
    form.send_confirmation_email()
    assert mock_send_note_confirmation.called_once()


def test_fulfill_order_line(order_with_lines_and_stock):
    order = order_with_lines_and_stock
    line = order.lines.first()
    stock = line.stock
    stock_quantity_after = stock.quantity - line.quantity
    fulfill_order_line(line, line.quantity)
    stock.refresh_from_db()
    assert stock.quantity == stock_quantity_after


def test_view_change_fulfillment_tracking(admin_client, fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    url = reverse(
        'dashboard:fulfillment-change-tracking', kwargs={
            'order_pk': fulfilled_order.pk,
            'fulfillment_pk': fulfillment.pk})
    tracking_number = '1234-5678AF'
    data = {'tracking_number': tracking_number}

    response = admin_client.post(url, data)

    fulfillment.refresh_from_db()
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse(
        'dashboard:order-details', kwargs={'order_pk': fulfilled_order.pk})
    assert fulfillment.tracking_number == tracking_number
