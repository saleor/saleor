from prices import Price

from saleor.cart.models import Cart
from saleor.order import models, OrderStatus
from saleor.order.utils import (
    add_variant_to_delivery_group, fill_group_with_partition)


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


def test_stock_allocation(billing_address, product_in_stock):
    variant = product_in_stock.variants.get()
    cart = Cart()
    cart.save()
    cart.add(variant, quantity=2)
    order = models.Order.objects.create(billing_address=billing_address)
    delivery_group = models.DeliveryGroup.objects.create(order=order)
    fill_group_with_partition(delivery_group, cart.lines.all())
    order_line = delivery_group.lines.get()
    stock = order_line.stock
    assert stock.quantity_allocated == 2


def test_order_discount(sale, order, request_cart_with_item):
    cart = request_cart_with_item
    group = models.DeliveryGroup.objects.create(order=order)
    fill_group_with_partition(
        group, cart.lines.all(), discounts=cart.discounts)
    line = group.lines.first()
    assert line.get_price_per_item() == Price(currency="USD", net=5)


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


def test_order_status_new(new_orders):
    assert all([order.status == OrderStatus.OPEN for order in new_orders])


def test_order_status_shipped(shipped_orders):
    assert all([
        order.status == OrderStatus.CLOSED for order in shipped_orders])


def test_order_status_cancelled(cancelled_orders):
    assert all([
        order.status == OrderStatus.CLOSED for order in cancelled_orders])


def test_order_queryset_new_orders(
        new_orders, shipped_orders, cancelled_orders):
    qs = models.Order.objects.new()
    assert qs.count() == len(new_orders)
    assert all([item in qs for item in new_orders])


def test_order_queryset_shipped_orders(
        new_orders, shipped_orders, cancelled_orders):
    qs = models.Order.objects.shipped()
    assert qs.count() == len(shipped_orders)
    assert all([item in qs for item in shipped_orders])


def test_order_queryset_cancelled_orders(
        new_orders, shipped_orders, cancelled_orders):
    qs = models.Order.objects.cancelled()
    assert qs.count() == len(cancelled_orders)
    assert all([item in qs for item in cancelled_orders])
