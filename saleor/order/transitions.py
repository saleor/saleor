from satchless.item import InsufficientStock

from saleor.order import GroupStatus
from saleor.product.models import Stock


def process_delivery_group(group, partition, discounts=None):
    """Fills shipment group with order lines created from partition items."""
    for item in partition:
        variant = item.variant
        quantity_left = item.get_quantity()
        price = variant.get_price_per_item(discounts)
        while quantity_left > 0:
            stock = variant.select_stockrecord()
            if not stock:
                raise InsufficientStock(variant)
            quantity = (
                stock.quantity_available
                if quantity_left > stock.quantity_available
                else quantity_left
            )
            group.lines.create(
                product=variant.product,
                product_name=variant.display_product(),
                product_sku=variant.sku,
                quantity=quantity,
                unit_price_net=price.net,
                unit_price_gross=price.gross,
                stock=stock,
                stock_location=stock.location.name)
            Stock.objects.allocate_stock(stock, quantity)
            # refresh stock for accessing quantity_allocated
            stock.refresh_from_db()
            quantity_left -= quantity


def cancel_delivery_group(group):
    """Cancels delivery group by returning products to stocks."""
    if group.status == GroupStatus.NEW:
        for line in group:
            Stock.objects.deallocate_stock(line.stock, line.quantity)
    elif group.status == GroupStatus.SHIPPED:
        for line in group:
            Stock.objects.increase_stock(line.stock, line.quantity)


def ship_delivery_group(group):
    """Ships delivery group by decreasing products in stocks."""
    for line in group.lines.all():
        Stock.objects.decrease_stock(line.stock, line.quantity)
