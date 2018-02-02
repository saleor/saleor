from decimal import Decimal
from django.urls import reverse
from prices import Price

from saleor.order import models, OrderStatus
from saleor.order.forms import OrderNoteForm
from saleor.order.utils import add_variant_to_delivery_group
from tests.utils import get_redirect_location


def test_total_property():
    order = models.Order(total_net=20, total_tax=5)
    assert order.total.gross == 25
    assert order.total.tax == 5
    assert order.total.net == 20


def test_total_property_empty_value():
    order = models.Order(total_net=None, total_tax=None)
    assert order.total is None


def test_total_setter():
    price = Price(net=10, gross=20, currency='USD')
    order = models.Order()
    order.total = price
    assert order.total_net.net == 10
    assert order.total_tax.net == 10


def test_add_variant_to_delivery_group_adds_line_for_new_variant(
        order_with_lines, product_in_stock):
    group = order_with_lines.groups.get()
    variant = product_in_stock.variants.get()
    lines_before = group.lines.count()

    add_variant_to_delivery_group(group, variant, 1)

    line = group.lines.last()
    assert group.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.quantity == 1


def test_add_variant_to_delivery_group_allocates_stock_for_new_variant(
        order_with_lines, product_in_stock):
    group = order_with_lines.groups.get()
    variant = product_in_stock.variants.get()
    stock = variant.select_stockrecord()
    stock_before = stock.quantity_allocated

    add_variant_to_delivery_group(group, variant, 1)

    stock.refresh_from_db()
    assert stock.quantity_allocated == stock_before + 1


def test_add_variant_to_delivery_group_edits_line_for_existing_variant(
        order_with_lines_and_stock):
    order = order_with_lines_and_stock
    group = order.groups.get()
    existing_line = group.lines.first()
    variant = existing_line.product.variants.get()
    lines_before = group.lines.count()
    line_quantity_before = existing_line.quantity

    add_variant_to_delivery_group(group, variant, 1)

    existing_line.refresh_from_db()
    assert group.lines.count() == lines_before
    assert existing_line.product_sku == variant.sku
    assert existing_line.quantity == line_quantity_before + 1


def test_add_variant_to_delivery_group_allocates_stock_for_existing_variant(
        order_with_lines_and_stock):
    order = order_with_lines_and_stock
    group = order.groups.get()
    existing_line = group.lines.first()
    variant = existing_line.product.variants.get()
    stock = existing_line.stock
    stock_before = stock.quantity_allocated

    add_variant_to_delivery_group(group, variant, 1)

    stock.refresh_from_db()
    assert stock.quantity_allocated == stock_before + 1


def test_order_status_open(open_orders):
    assert all([order.status == OrderStatus.OPEN for order in open_orders])


def test_order_status_closed(closed_orders):
    assert all([order.status == OrderStatus.CLOSED for order in closed_orders])


def test_order_queryset_open_orders(open_orders, closed_orders):
    qs = models.Order.objects.open()
    assert qs.count() == len(open_orders)
    assert all([item in qs for item in open_orders])


def test_order_queryset_closed_orders(open_orders, closed_orders):
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
    assert redirect_location == reverse('profile:details')
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
    order.create_history_entry(content='test_entry')
    history_entry = models.OrderHistoryEntry.objects.get(order=order)
    assert history_entry == order.history.first()
    assert history_entry.content == 'test_entry'


def test_delivery_group_is_shipping_required(delivery_group):
    assert delivery_group.is_shipping_required()


def test_delivery_group_is_shipping_required_no_shipping(delivery_group):
    line = delivery_group.lines.first()
    line.is_shipping_required = False
    line.save()
    assert not delivery_group.is_shipping_required()


def test_delivery_group_is_shipping_required_partially_required(
        delivery_group, product_without_shipping):
    variant = product_without_shipping.variants.get()
    product_type = product_without_shipping.product_type
    delivery_group.lines.create(
        delivery_group=delivery_group,
        product=product_without_shipping,
        product_name=product_without_shipping.name,
        product_sku=variant.sku,
        is_shipping_required=product_type.is_shipping_required,
        quantity=3,
        unit_price_net=Decimal('30.00'),
        unit_price_gross=Decimal('30.00'))
    assert delivery_group.is_shipping_required()
