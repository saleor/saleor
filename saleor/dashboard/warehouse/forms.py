from django import forms

from saleor.warehouse.models import Warehouse


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = [
            "name",
            "company_name",
            "shipping_zones",
            "street_address",
            "city",
            "postal_code",
            "country",
            "country_area",
            "email",
            "phone",
        ]
