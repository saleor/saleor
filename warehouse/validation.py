from ..shipping.models import ShippingZone
from .models import Warehouse


def validate_warehouse_count(shipping_zones, instance: Warehouse) -> bool:
    """Every ShippingZone can be assigned to only one warehouse.

    If not there would be issue with automatically selecting stock for operation.
    """

    warehouses = set(
        ShippingZone.objects.filter(
            id__in=[shipping_zone.id for shipping_zone in shipping_zones]
        )
        .filter(warehouses__isnull=False)
        .values_list("warehouses", flat=True)
    )
    if not bool(warehouses):
        return True
    if len(warehouses) > 1:
        return False
    if instance.id is None:
        return False
    return warehouses == {instance.id}
