from decimal import Decimal
from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse
from payments import PaymentStatus
from prices import Money, TaxedMoney
from tests.utils import get_form_errors, get_redirect_location

from saleor.core.utils import ZERO_TAXED_MONEY
from saleor.dashboard.order.forms import ChangeQuantityForm, OrderNoteForm
from saleor.dashboard.order.utils import (
    fulfill_order_line, remove_customer_from_order, save_address_in_order,
    update_order_with_user_addresses)
from saleor.discount.utils import increase_voucher_usage
from saleor.order import OrderStatus
from saleor.order.models import Order, OrderLine, OrderNote
from saleor.order.utils import (
    add_variant_to_existing_lines, add_variant_to_order,
    change_order_line_quantity)
from saleor.product.models import ProductVariant, Stock, StockLocation


@pytest.mark.integration
@pytest.mark.django_db
def test_view_capture_order_payment_preauth(
        admin_client, order_with_lines, payment_preauth):
    order = order_with_lines
    url = reverse(
        'dashboard:capture-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_preauth.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {
            'csrfmiddlewaretoken': 'hello',
            'amount': str(order.total.gross.amount)})
    assert response.status_code == 302
    assert order.payments.last().status == PaymentStatus.CONFIRMED
    assert order.payments.last().get_captured_price() == order.total


@pytest.mark.integration
@pytest.mark.django_db
def test_view_capture_order_invalid_payment_waiting_status(
        admin_client, order_with_lines, payment_waiting):
    order = order_with_lines
    url = reverse(
        'dashboard:capture-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_waiting.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.WAITING


@pytest.mark.integration
@pytest.mark.django_db
def test_view_capture_order_invalid_payment_confirmed_status(
        admin_client, order_with_lines, payment_confirmed):
    order = order_with_lines
    url = reverse(
        'dashboard:capture-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_confirmed.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.CONFIRMED


@pytest.mark.integration
@pytest.mark.django_db
def test_view_capture_order_invalid_payment_rejected_status(
        admin_client, order_with_lines, payment_rejected):
    order = order_with_lines
    url = reverse(
        'dashboard:capture-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_rejected.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.REJECTED


@pytest.mark.integration
@pytest.mark.django_db
def test_view_capture_order_invalid_payment_refunded_status(
        admin_client, order_with_lines, payment_refunded):
    order = order_with_lines
    url = reverse(
        'dashboard:capture-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_refunded.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.REFUNDED


@pytest.mark.integration
@pytest.mark.django_db
def test_view_capture_order_invalid_payment_error_status(
        admin_client, order_with_lines, payment_error):
    order = order_with_lines
    url = reverse(
        'dashboard:capture-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_error.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.ERROR


@pytest.mark.integration
@pytest.mark.django_db
def test_view_capture_order_invalid_payment_input_status(
        admin_client, order_with_lines, payment_input):
    order = order_with_lines
    url = reverse(
        'dashboard:capture-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_input.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.INPUT


@pytest.mark.integration
@pytest.mark.django_db
def test_view_refund_order_payment_confirmed(
        admin_client, order_with_lines, payment_confirmed):
    order = order_with_lines

    url = reverse(
        'dashboard:refund-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_confirmed.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {
            'csrfmiddlewaretoken': 'hello',
            'amount': str(payment_confirmed.captured_amount)})
    assert response.status_code == 302
    assert order.payments.last().status == PaymentStatus.REFUNDED
    assert order.payments.last().get_captured_price() == TaxedMoney(
        net=Money(0, 'USD'), gross=Money(0, 'USD'))


@pytest.mark.integration
@pytest.mark.django_db
def test_view_refund_order_invalid_payment_waiting_status(
        admin_client, order_with_lines, payment_waiting):
    order = order_with_lines

    url = reverse(
        'dashboard:refund-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_waiting.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.WAITING


@pytest.mark.integration
@pytest.mark.django_db
def test_view_refund_order_invalid_payment_preauth_status(
        admin_client, order_with_lines, payment_preauth):
    order = order_with_lines

    url = reverse(
        'dashboard:refund-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_preauth.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.PREAUTH


@pytest.mark.integration
@pytest.mark.django_db
def test_view_refund_order_invalid_payment_rejected_status(
        admin_client, order_with_lines, payment_rejected):
    order = order_with_lines

    url = reverse(
        'dashboard:refund-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_rejected.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.REJECTED


@pytest.mark.integration
@pytest.mark.django_db
def test_view_refund_order_invalid_payment_refunded_status(
        admin_client, order_with_lines, payment_refunded):
    order = order_with_lines

    url = reverse(
        'dashboard:refund-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_refunded.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.REFUNDED


@pytest.mark.integration
@pytest.mark.django_db
def test_view_refund_order_invalid_payment_error_status(
        admin_client, order_with_lines, payment_error):
    order = order_with_lines

    url = reverse(
        'dashboard:refund-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_error.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.ERROR


@pytest.mark.integration
@pytest.mark.django_db
def test_view_refund_order_invalid_payment_input_status(
        admin_client, order_with_lines, payment_input):
    order = order_with_lines

    url = reverse(
        'dashboard:refund-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_input.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello', 'amount': '20.00'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.INPUT


@pytest.mark.integration
@pytest.mark.django_db
def test_view_release_order_payment_preauth(
        admin_client, order_with_lines, payment_preauth):
    order = order_with_lines

    url = reverse(
        'dashboard:release-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_preauth.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, {
        'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 302
    assert order.payments.last().status == PaymentStatus.REFUNDED
    assert order.payments.last().get_captured_price() == TaxedMoney(
        net=Money(0, 'USD'), gross=Money(0, 'USD'))


@pytest.mark.integration
@pytest.mark.django_db
def test_view_release_order_invalid_payment_waiting_status(
        admin_client, order_with_lines, payment_waiting):
    order = order_with_lines

    url = reverse(
        'dashboard:release-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_waiting.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, {
        'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.WAITING


@pytest.mark.integration
@pytest.mark.django_db
def test_view_release_order_invalid_payment_confirmed_status(
        admin_client, order_with_lines, payment_confirmed):
    order = order_with_lines

    url = reverse(
        'dashboard:release-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_confirmed.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, {
        'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.CONFIRMED


@pytest.mark.integration
@pytest.mark.django_db
def test_view_release_order_invalid_payment_rejected_status(
        admin_client, order_with_lines, payment_rejected):
    order = order_with_lines

    url = reverse(
        'dashboard:release-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_rejected.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, {
        'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.REJECTED


@pytest.mark.integration
@pytest.mark.django_db
def test_view_release_order_invalid_payment_refunded_status(
        admin_client, order_with_lines, payment_refunded):
    order = order_with_lines

    url = reverse(
        'dashboard:release-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_refunded.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, {
        'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.REFUNDED


@pytest.mark.integration
@pytest.mark.django_db
def test_view_release_order_invalid_payment_error_status(
        admin_client, order_with_lines, payment_error):
    order = order_with_lines

    url = reverse(
        'dashboard:release-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_error.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, {
        'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.ERROR


@pytest.mark.integration
@pytest.mark.django_db
def test_view_release_order_invalid_payment_input_status(
        admin_client, order_with_lines, payment_input):
    order = order_with_lines

    url = reverse(
        'dashboard:release-payment', kwargs={
            'order_pk': order.pk, 'payment_pk': payment_input.pk})
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, {
        'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 400
    assert order.payments.last().status == PaymentStatus.INPUT


@pytest.mark.integration
@pytest.mark.django_db
def test_view_cancel_order_line(admin_client, draft_order):
    lines_before = draft_order.lines.all()
    lines_before_count = lines_before.count()
    line = lines_before.first()
    line_quantity = line.quantity
    quantity_allocated_before = line.stock.quantity_allocated
    product = line.product

    url = reverse(
        'dashboard:orderline-cancel', kwargs={
            'order_pk': draft_order.pk,
            'line_pk': line.pk})

    response = admin_client.get(url)
    assert response.status_code == 200
    response = admin_client.post(url, {'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse(
        'dashboard:order-details', args=[draft_order.pk])
    # check ordered item removal
    lines_after = Order.objects.get().lines.all()
    assert lines_before_count - 1 == lines_after.count()
    # check stock deallocation
    assert Stock.objects.first().quantity_allocated == (
        quantity_allocated_before - line_quantity)
    url = reverse(
        'dashboard:orderline-cancel', kwargs={
            'order_pk': draft_order.pk,
            'line_pk': OrderLine.objects.get().pk})
    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello'}, follow=True)
    assert Order.objects.get().lines.all().count() == 0
    # check success messages after redirect
    assert response.context['messages']


@pytest.mark.integration
@pytest.mark.django_db
def test_view_change_order_line_quantity(admin_client, draft_order):
    lines_before_quantity_change = draft_order.lines.all()
    lines_before_quantity_change_count = lines_before_quantity_change.count()
    line = lines_before_quantity_change.first()

    url = reverse(
        'dashboard:orderline-change-quantity', kwargs={
            'order_pk': draft_order.pk,
            'line_pk': line.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    response = admin_client.post(
        url, {'quantity': 2}, follow=True)
    redirected_to, redirect_status_code = response.redirect_chain[-1]
    # check redirection
    assert redirect_status_code == 302
    assert redirected_to == reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.id})
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


@pytest.mark.integration
@pytest.mark.django_db
def test_view_change_order_line_quantity_with_invalid_data(
        admin_client, draft_order):
    lines = draft_order.lines.all()
    line = lines.first()
    url = reverse(
        'dashboard:orderline-change-quantity', kwargs={
            'order_pk': draft_order.pk,
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
    change_order_line_quantity(lines[1], 0)
    change_order_line_quantity(lines[0], 0)
    assert order_with_lines.get_total_quantity() == 0


@pytest.mark.integration
@pytest.mark.django_db
def test_view_order_invoice(admin_client, order_with_lines):
    url = reverse(
        'dashboard:order-invoice', kwargs={
            'order_pk': order_with_lines.id})
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/pdf'
    name = "invoice-%s" % order_with_lines.id
    assert response['Content-Disposition'] == 'filename=%s' % name


@pytest.mark.integration
@pytest.mark.django_db
def test_view_order_invoice_without_shipping(admin_client, order_with_lines):
    order_with_lines.shipping_address.delete()
    # Regression test for #1536:
    url = reverse(
        'dashboard:order-invoice', kwargs={'order_pk': order_with_lines.id})
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/pdf'


@pytest.mark.integration
@pytest.mark.django_db
def test_view_fulfillment_packing_slips(admin_client, fulfilled_order):
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
        admin_client, fulfilled_order):
    # Regression test for #1536
    fulfilled_order.shipping_address.delete()
    fulfillment = fulfilled_order.fulfillments.first()
    url = reverse(
        'dashboard:fulfillment-packing-slips', kwargs={
            'order_pk': fulfilled_order.pk, 'fulfillment_pk': fulfillment.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/pdf'


@pytest.mark.integration
@pytest.mark.django_db
def test_view_change_order_line_stock_valid(admin_client, draft_order):
    line = draft_order.lines.last()
    old_stock = line.stock
    variant = ProductVariant.objects.get(sku=line.product_sku)
    stock_location = StockLocation.objects.create(name='Warehouse 2')
    stock = Stock.objects.create(
        variant=variant, cost_price=2, quantity=2, quantity_allocated=0,
        location=stock_location)

    url = reverse(
        'dashboard:orderline-change-stock', kwargs={
            'order_pk': draft_order.pk,
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
        admin_client, draft_order):
    line = draft_order.lines.last()
    old_stock = line.stock
    variant = ProductVariant.objects.get(sku=line.product_sku)
    stock_location = StockLocation.objects.create(name='Warehouse 2')
    stock = Stock.objects.create(
        variant=variant, cost_price=2, quantity=2, quantity_allocated=1,
        location=stock_location)

    url = reverse(
        'dashboard:orderline-change-stock', kwargs={
            'order_pk': draft_order.pk,
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


def test_view_change_order_line_stock_merges_lines(admin_client, draft_order):
    line = draft_order.lines.first()
    old_stock = line.stock
    variant = ProductVariant.objects.get(sku=line.product_sku)
    stock_location = StockLocation.objects.create(name='Warehouse 2')
    stock = Stock.objects.create(
        variant=variant, cost_price=2, quantity=2, quantity_allocated=2,
        location=stock_location)
    line_2 = draft_order.lines.create(
        product=line.product,
        product_name=line.product.name,
        product_sku='SKU_A',
        is_shipping_required=line.is_shipping_required,
        quantity=2,
        unit_price_net=Decimal('30.00'),
        unit_price_gross=Decimal('30.00'),
        stock=stock,
        stock_location=stock.location.name)
    lines_before = draft_order.lines.count()

    url = reverse(
        'dashboard:orderline-change-stock', kwargs={
            'order_pk': draft_order.pk,
            'line_pk': line_2.pk})
    data = {'stock': old_stock.pk}
    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert draft_order.lines.count() == lines_before - 1

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
    order.status = OrderStatus.DRAFT
    order.save()
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
        mock_send_note_confirmation, order_with_lines):
    order = order_with_lines
    note = OrderNote(order=order, user=order.user)
    form = OrderNoteForm({'content': 'test_note'}, instance=note)
    form.send_confirmation_email()
    assert mock_send_note_confirmation.called_once()


def test_fulfill_order_line(order_with_lines):
    order = order_with_lines
    line = order.lines.first()
    quantity_fulfilled_before = line.quantity_fulfilled
    stock = line.stock
    stock_quantity_after = stock.quantity - line.quantity

    fulfill_order_line(line, line.quantity)

    stock.refresh_from_db()
    assert stock.quantity == stock_quantity_after
    assert line.quantity_fulfilled == quantity_fulfilled_before + line.quantity


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


@pytest.mark.django_db
def test_view_order_create(admin_client):
    url = reverse('dashboard:order-create')

    response = admin_client.post(url, {})

    assert response.status_code == 302
    assert Order.objects.count() == 1
    order = Order.objects.first()
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': order.pk})
    assert get_redirect_location(response) == redirect_url
    assert order.status == OrderStatus.DRAFT


@pytest.mark.django_db
def test_view_create_from_draft_order_valid(admin_client, draft_order):
    order = draft_order
    url = reverse(
        'dashboard:create-order-from-draft', kwargs={'order_pk': order.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': order.pk})
    assert get_redirect_location(response) == redirect_url


@pytest.mark.django_db
def test_view_create_from_draft_order_assigns_customer_email(
        admin_client, draft_order, customer_user):
    order = draft_order
    order.user_email = ''
    order.save()
    url = reverse(
        'dashboard:create-order-from-draft', kwargs={'order_pk': order.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    admin_client.post(url, data)

    order.refresh_from_db()
    assert order.user_email == customer_user.email


@pytest.mark.django_db
def test_view_create_from_draft_order_empty_order(admin_client, draft_order):
    order = draft_order
    order.lines.all().delete()
    url = reverse(
        'dashboard:create-order-from-draft', kwargs={'order_pk': order.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    response = admin_client.post(url, data)

    assert response.status_code == 400
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT
    errors = get_form_errors(response)
    assert 'Could not create order without any products' in errors


@pytest.mark.django_db
def test_view_create_from_draft_order_not_draft_order(
        admin_client, order_with_lines):
    url = reverse(
        'dashboard:create-order-from-draft',
        kwargs={'order_pk': order_with_lines.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    response = admin_client.post(url, data)

    assert response.status_code == 404


@pytest.mark.django_db
def test_view_create_from_draft_order_shipping_method_not_valid(
        admin_client, draft_order, shipping_method):
    method = shipping_method.price_per_country.create(
        country_code='DE', price=10)
    draft_order.shipping_method = method
    draft_order.save()
    url = reverse(
        'dashboard:create-order-from-draft',
        kwargs={'order_pk': draft_order.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    response = admin_client.post(url, data)

    assert response.status_code == 400
    draft_order.refresh_from_db()
    assert draft_order.status == OrderStatus.DRAFT
    errors = get_form_errors(response)
    error = 'Shipping method is not valid for chosen shipping address'
    assert error in errors


@pytest.mark.django_db
def test_view_create_from_draft_order_no_shipping_address_shipping_not_required(  # noqa
        admin_client, draft_order):
    url = reverse(
        'dashboard:create-order-from-draft',
        kwargs={'order_pk': draft_order.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    draft_order.refresh_from_db()
    assert draft_order.status == OrderStatus.UNFULFILLED
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url


@pytest.mark.django_db
def test_view_order_customer_edit_to_existing_user(
        admin_client, customer_user, draft_order):
    draft_order.user = None
    draft_order.save()
    url = reverse(
        'dashboard:order-customer-edit', kwargs={'order_pk': draft_order.pk})
    data = {
        'user_email': '', 'user': customer_user.pk, 'update_addresses': True}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    draft_order.refresh_from_db()
    assert draft_order.user == customer_user
    assert not draft_order.user_email
    assert (
        draft_order.billing_address == customer_user.default_billing_address)
    assert (
        draft_order.shipping_address == customer_user.default_shipping_address)
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url


@pytest.mark.django_db
def test_view_order_customer_edit_to_email(admin_client, draft_order):
    url = reverse(
        'dashboard:order-customer-edit', kwargs={'order_pk': draft_order.pk})
    data = {
        'user_email': 'customer@example.com', 'user': '',
        'update_addresses': False}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    draft_order.refresh_from_db()
    assert draft_order.user_email == 'customer@example.com'
    assert not draft_order.user
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url


@pytest.mark.django_db
def test_view_order_customer_edit_to_guest_customer(admin_client, draft_order):
    url = reverse(
        'dashboard:order-customer-edit', kwargs={'order_pk': draft_order.pk})
    data = {'user_email': '', 'user': '', 'update_addresses': False}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    draft_order.refresh_from_db()
    assert not draft_order.user_email
    assert not draft_order.user
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url


@pytest.mark.django_db
def test_view_order_customer_edit_not_valid(
        admin_client, customer_user, draft_order):
    draft_order.user = None
    draft_order.user_email = ''
    draft_order.save()
    url = reverse(
        'dashboard:order-customer-edit', kwargs={'order_pk': draft_order.pk})
    data = {
        'user_email': 'customer@example.com', 'user': customer_user.pk,
        'update_addresses': False}

    response = admin_client.post(url, data)

    assert response.status_code == 400
    draft_order.refresh_from_db()
    assert not draft_order.user == customer_user
    errors = get_form_errors(response)
    error = (
        'An order can be related either with an email or an existing user '
        'account')
    assert error in errors


@pytest.mark.django_db
def test_view_order_customer_remove(admin_client, draft_order):
    url = reverse(
        'dashboard:order-customer-remove', kwargs={'order_pk': draft_order.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url
    draft_order.refresh_from_db()
    assert not draft_order.user
    assert not draft_order.user_email
    assert not draft_order.billing_address
    assert not draft_order.shipping_address


@pytest.mark.django_db
def test_view_order_shipping_edit(
        admin_client, draft_order, shipping_method, settings):
    method = shipping_method.price_per_country.create(
        price=Money(5, settings.DEFAULT_CURRENCY), country_code='PL')
    url = reverse(
        'dashboard:order-shipping-edit', kwargs={'order_pk': draft_order.pk})
    data = {'shipping_method': method.pk}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url
    draft_order.refresh_from_db()
    assert draft_order.shipping_method_name == shipping_method.name
    assert draft_order.shipping_price == method.get_total_price()
    assert draft_order.shipping_method == method


@pytest.mark.django_db
def test_view_order_shipping_edit_not_draft_order(
        admin_client, order_with_lines, shipping_method):
    method = shipping_method.price_per_country.create(
        price=5, country_code='PL')
    url = reverse(
        'dashboard:order-shipping-edit',
        kwargs={'order_pk': order_with_lines.pk})
    data = {'shipping_method': method.pk}

    response = admin_client.post(url, data)

    assert response.status_code == 404


@pytest.mark.django_db
def test_view_order_shipping_remove(admin_client, draft_order):
    url = reverse(
        'dashboard:order-shipping-remove', kwargs={'order_pk': draft_order.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url
    draft_order.refresh_from_db()
    assert not draft_order.shipping_method
    assert not draft_order.shipping_method_name
    assert draft_order.shipping_price == ZERO_TAXED_MONEY


@pytest.mark.django_db
def test_view_remove_draft_order(admin_client, draft_order):
    url = reverse(
        'dashboard:draft-order-delete', kwargs={'order_pk': draft_order.pk})

    response = admin_client.post(url, {})

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:orders')
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_view_remove_draft_order_invalid(admin_client, order_with_lines):
    url = reverse(
        'dashboard:draft-order-delete',
        kwargs={'order_pk': order_with_lines.pk})

    response = admin_client.post(url, {})

    assert response.status_code == 404
    assert Order.objects.count() == 1


@pytest.mark.django_db
def test_view_edit_discount(admin_client, draft_order, settings):
    discount_value = 5
    total_before = draft_order.total
    url = reverse(
        'dashboard:order-discount-edit',
        kwargs={'order_pk': draft_order.pk})
    data = {'discount_amount': discount_value}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url

    draft_order.refresh_from_db()
    discount_amount = Money(discount_value, settings.DEFAULT_CURRENCY)
    assert draft_order.discount_amount == discount_amount
    assert draft_order.total == total_before - discount_amount


def test_update_order_with_user_addresses(order):
    update_order_with_user_addresses(order)
    assert order.billing_address == order.user.default_billing_address
    assert order.shipping_address == order.user.default_shipping_address


def test_update_order_with_user_addresses_empty_user(order):
    order.user = None
    order.save()
    update_order_with_user_addresses(order)
    assert order.billing_address is None
    assert order.shipping_address is None


def test_save_address_in_order_shipping_address(order, address):
    old_billing_address = order.billing_address
    address.first_name = 'Jane'
    address.save()

    save_address_in_order(order, address, 'shipping')

    assert order.shipping_address == address
    assert order.shipping_address.pk == address.pk
    assert order.billing_address == old_billing_address


def test_save_address_in_order_billing_address(order, address):
    address.first_name = 'Jane'
    address.save()

    save_address_in_order(order, address, 'billing')

    assert order.billing_address == address
    assert order.billing_address.pk == address.pk
    assert order.shipping_address == order.billing_address


def test_remove_customer_from_order(order):
    remove_customer_from_order(order)

    assert order.user is None
    assert order.user_email == ''
    assert order.billing_address is None


def test_remove_customer_from_order_remove_addresses(order, customer_user):
    order.billing_address = customer_user.default_billing_address.get_copy()
    order.shipping_address = customer_user.default_shipping_address.get_copy()

    remove_customer_from_order(order)

    assert order.user is None
    assert order.user_email == ''
    assert order.billing_address is None
    assert order.shipping_address is None


def test_remove_customer_from_order_do_not_remove_modified_addresses(
        order, customer_user):
    order.billing_address = customer_user.default_billing_address.get_copy()
    order.billing_address.first_name = 'Jane'
    order.billing_address.save()
    old_billing_address = order.billing_address

    order.shipping_address = customer_user.default_shipping_address.get_copy()
    order.shipping_address.first_name = 'Jane'
    order.shipping_address.save()
    old_shipping_address = order.shipping_address

    remove_customer_from_order(order)

    assert order.user is None
    assert order.user_email == ''
    assert order.billing_address == old_billing_address
    assert order.shipping_address == old_shipping_address


def test_view_order_voucher_edit(admin_client, draft_order, voucher):
    total_before = draft_order.total
    url = reverse(
        'dashboard:order-voucher-edit', kwargs={'order_pk': draft_order.pk})
    data = {'voucher': voucher.pk}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url

    draft_order.refresh_from_db()
    discount_amount = Money(voucher.discount_value, settings.DEFAULT_CURRENCY)
    assert draft_order.discount_amount == discount_amount
    assert draft_order.total == total_before - discount_amount


def test_view_order_voucher_remove(admin_client, draft_order, voucher):
    increase_voucher_usage(voucher)
    draft_order.voucher = voucher
    discount_amount = Money(voucher.discount_value, settings.DEFAULT_CURRENCY)
    draft_order.discount_amount = discount_amount
    draft_order.total -= discount_amount
    draft_order.save()
    total_before = draft_order.total
    url = reverse(
        'dashboard:order-voucher-remove', kwargs={'order_pk': draft_order.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': draft_order.pk})
    assert get_redirect_location(response) == redirect_url

    draft_order.refresh_from_db()
    assert draft_order.discount_amount == Money(0, settings.DEFAULT_CURRENCY)
    assert draft_order.total == total_before + discount_amount


def test_view_mark_order_as_paid(admin_client, order_with_lines):
    url = reverse(
        'dashboard:order-mark-as-paid',
        kwargs={'order_pk': order_with_lines.pk})
    data = {'csrfmiddlewaretoken': 'hello'}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:order-details', kwargs={'order_pk': order_with_lines.pk})
    assert get_redirect_location(response) == redirect_url

    order_with_lines.refresh_from_db()
    assert order_with_lines.is_fully_paid()
    assert order_with_lines.history.filter(
        content='Order manually marked as paid').exists()
