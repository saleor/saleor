from unittest.mock import Mock

from django.urls import reverse
from prices import Money, TaxedMoney
from tests.utils import get_redirect_location

from saleor.order import OrderStatus, models
from saleor.order.emails import collect_data_for_email
from saleor.order.forms import OrderNoteForm
from saleor.order.utils import recalculate_order


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


def test_order_status_open(open_orders):
    assert all([order.status == OrderStatus.OPEN for order in open_orders])


def test_order_status_closed(closed_orders):
    assert all([order.status == OrderStatus.CLOSED for order in closed_orders])


def test_order_queryset_open_orders(open_orders):
    qs = models.Order.objects.open()
    assert qs.count() == len(open_orders)
    assert all([item in qs for item in open_orders])


def test_order_queryset_closed_orders(closed_orders):
    qs = models.Order.objects.closed()
    assert qs.count() == len(closed_orders)
    assert all([item in qs for item in closed_orders])


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
    assert order.is_open
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
