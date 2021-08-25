from ...shipping.models import ShippingZone
from ..models import Warehouse


def test_get_first_warehouse_for_channel_no_shipping_zone(
    warehouses_with_different_shipping_zone, channel_USD
):
    for shipping_zone in ShippingZone.objects.all():
        shipping_zone.channels.all().delete()
    # At this point warehouse has no shipping zones; getting the first warehouse for
    # channel should return None.
    warehouse = Warehouse.objects.get_first_warehouse_for_channel(channel_USD.pk)
    assert warehouse is None


def test_get_first_warehouse_for_channel(warehouses, channel_USD):
    warehouse_usa = warehouses[1]
    shipping_zone = ShippingZone.objects.create(name="USA", countries=["US"])
    shipping_zone.channels.add(channel_USD)
    warehouse_usa.shipping_zones.add(shipping_zone)

    first_warehouse = Warehouse.objects.get_first_warehouse_for_channel(channel_USD.pk)
    assert first_warehouse == warehouse_usa
