from django import forms

from ....product.models import Product


class ProductForm(forms.ModelForm):
    """Base form for creating products without specific."""
    class Meta:
        model = Product
        exclude = ['updated_at']
