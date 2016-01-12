from django import forms
from ...product.models import FixedProductDiscount


class FixedProductDiscountForm(forms.ModelForm):
    class Meta:
        model = FixedProductDiscount
        fields = ['name', 'products', 'categories',
                  'discount', 'percentage_discount']
