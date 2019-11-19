from django import forms

from ...account.models import Address
from ...warehouse.models import Warehouse


class WarehouseAddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "street_address_1",
            "street_address_2",
            "city",
            "city_area",
            "postal_code",
            "country",
            "country_area",
            "phone",
        ]


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ["name", "email", "shipping_zones", "company_name"]

    def save_with_address(self, address: Address, commit: bool = True):
        self.instance.address = address
        self.save(commit)
        return self.instance


def save_warehouse_from_forms(
    warehouse_form: WarehouseForm, address_form: WarehouseAddressForm
) -> Warehouse:
    address = address_form.save()
    return warehouse_form.save_with_address(address)
