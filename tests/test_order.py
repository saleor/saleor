from prices import Price

from saleor.order import models, OrderStatus
from saleor.order.utils import add_variant_to_delivery_group


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
