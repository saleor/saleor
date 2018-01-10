from saleor.order import GroupStatus
from saleor.order.utils import add_variant_to_delivery_group
from saleor.product.utils import (
    deallocate_stock, decrease_stock, increase_stock)


def process_delivery_group(group, cart_lines, discounts=None):
    """Fills shipment group with order lines created from partition items."""
    for line in cart_lines:
        add_variant_to_delivery_group(
            group, line.variant, line.get_quantity(), discounts,
            add_to_existing=False)


def cancel_delivery_group(group):
    """Cancels delivery group by returning products to stocks."""
    if group.status == GroupStatus.NEW:
        for line in group:
            if line.stock:
                deallocate_stock(line.stock, line.quantity)
    elif group.status == GroupStatus.SHIPPED:
        for line in group:
            if line.stock:
                increase_stock(line.stock, line.quantity)


def ship_delivery_group(group, tracking_number=''):
    """Ships delivery group by decreasing products in stocks."""
    for line in group.lines.all():
        if line.stock:
            decrease_stock(line.stock, line.quantity)
    group.tracking_number = tracking_number
