from saleor.order import GroupStatus
from saleor.product.models import Stock


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
