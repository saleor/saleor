from django import forms

from ...shipping.models import ShippingZone
from ...warehouse.models import Warehouse


def get_available_shipping_zones():
    return ShippingZone.objects.filter(warehouse__isnull=True)


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ["name", "company_name", "shipping_zones", "email"]

    def validate_warehouse_count(self, shipping_zones) -> bool:
        warehouses = set(
            shipping_zones.filter(warehouse__isnull=False).values_list(
                "warehouse", flat=True
            )
        )
        if not bool(warehouses):
            return True
        if len(warehouses) > 1:
            return False
        instance_id = self.instance.id
        if instance_id is None:
            return False
        return warehouses == {instance_id}

    def clean_shipping_zones(self):
        shipping_zones = self.cleaned_data["shipping_zones"]
        if not self.validate_warehouse_count(shipping_zones):
            raise forms.ValidationError(
                "Shipping zone can be assigned only to one warehouse."
            )
        return shipping_zones
