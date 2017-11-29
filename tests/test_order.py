from __future__ import unicode_literals

from prices import Price

from saleor.cart.models import Cart
from saleor.order import models
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
    order_line = delivery_group.items.get()
    stock = order_line.stock
    assert stock.quantity_allocated == 2


def test_order_discount(sale, order, request_cart_with_item):
    cart = request_cart_with_item
    group = models.DeliveryGroup.objects.create(order=order)
    fill_group_with_partition(
        group, cart.lines.all(), discounts=cart.discounts)
    item = group.items.first()
    assert item.get_price_per_item() == Price(currency="USD", net=5)


def test_add_variant_to_delivery_group_adds_item_for_new_variant(
        order_with_items, product_in_stock):
    group = order_with_items.groups.get()
    variant = product_in_stock.variants.get()
    items_before = group.items.count()

    add_variant_to_delivery_group(group, variant, 1)

    item = group.items.last()
    assert group.items.count() == items_before + 1
    assert item.product_sku == variant.sku
    assert item.quantity == 1


def test_add_variant_to_delivery_group_allocates_stock_for_new_variant(
        order_with_items, product_in_stock):
    group = order_with_items.groups.get()
    variant = product_in_stock.variants.get()
    stock = variant.select_stockrecord()
    stock_before = stock.quantity_allocated

    add_variant_to_delivery_group(group, variant, 1)

    stock.refresh_from_db()
    assert stock.quantity_allocated == stock_before + 1


def test_add_variant_to_delivery_group_edits_item_for_existing_variant(
        order_with_items_and_stock):
    order = order_with_items_and_stock
    group = order.groups.get()
    existing_item = group.items.first()
    variant = existing_item.product.variants.get()
    items_before = group.items.count()
    item_quantity_before = existing_item.quantity

    add_variant_to_delivery_group(group, variant, 1)

    existing_item.refresh_from_db()
    assert group.items.count() == items_before
    assert existing_item.product_sku == variant.sku
    assert existing_item.quantity == item_quantity_before + 1


def test_add_variant_to_delivery_group_allocates_stock_for_existing_variant(
        order_with_items_and_stock):
    order = order_with_items_and_stock
    group = order.groups.get()
    existing_item = group.items.first()
    variant = existing_item.product.variants.get()
    stock = existing_item.stock
    stock_before = stock.quantity_allocated

    add_variant_to_delivery_group(group, variant, 1)

    stock.refresh_from_db()
    assert stock.quantity_allocated == stock_before + 1
