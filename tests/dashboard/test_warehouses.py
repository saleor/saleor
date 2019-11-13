import pytest
from django.db.utils import IntegrityError

from saleor.dashboard.warehouse.forms import WarehouseForm
from saleor.warehouse.models import Warehouse


def test_warehouse_form_will_fail_when_no_address(shipping_zone):
    data = {
        "name": "Test",
        "shipping_zones": [shipping_zone],
        "email": "warehouse@example.com",
    }
    form = WarehouseForm(data)
    assert form.is_valid()
    with pytest.raises(IntegrityError):
        form.save()


def test_warehouse_form_create_object(address, shipping_zone):
    data = {
        "name": "Test",
        "shipping_zones": [shipping_zone],
        "email": "warehouse@example.com",
    }
    assert not Warehouse.objects.exists()
    form = WarehouseForm(data)
    assert form.is_valid()
    # warehouse must have address
    form.save_with_address(address)
    assert Warehouse.objects.count() == 1


def test_warehouse_form_updates_object(warehouse, shipping_zone):
    assert warehouse.shipping_zones.count() == 1
    assert warehouse.shipping_zones.first() == shipping_zone
    new_name = "New name"
    data = {"name": new_name, "shipping_zones": [], "email": warehouse.email}
    form = WarehouseForm(data, instance=warehouse)
    assert form.is_valid()
    form.save()
    warehouse.refresh_from_db()
    assert warehouse.name == new_name
    assert not warehouse.shipping_zones.exists()
