from prices import Price

from saleor.cart.models import Cart
from saleor.dashboard.order.forms import ChangeQuantityForm
from saleor.order import models


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
    delivery_group.add_items_from_partition(cart.lines.all())
    order_line = delivery_group.items.get()
    stock = order_line.stock
    assert stock.quantity_allocated == 2


def test_dashboard_change_quantity_form(request_cart_with_item, order):
    cart = request_cart_with_item
    group = models.DeliveryGroup.objects.create(order=order)
    group.add_items_from_partition(cart.lines.all())
    order_line = group.items.get()

    # Check available quantity validation
    form = ChangeQuantityForm({'quantity': 9999},
                              instance=order_line)
    assert not form.is_valid()
    assert group.items.get().stock.quantity_allocated == 1
    # Save same quantity
    form = ChangeQuantityForm({'quantity': 1},
                              instance=order_line)
    assert form.is_valid()
    form.save()
    assert group.items.get().stock.quantity_allocated == 1
    # Increase quantity
    form = ChangeQuantityForm({'quantity': 2},
                              instance=order_line)
    assert form.is_valid()
    form.save()
    assert group.items.get().stock.quantity_allocated == 2
    # Decrease quantity
    form = ChangeQuantityForm({'quantity': 1},
                              instance=order_line)
    assert form.is_valid()
    form.save()
    assert group.items.get().stock.quantity_allocated == 1
