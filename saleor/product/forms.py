from django import forms

from ..cart.forms import AddToCartForm
from .models import Bag, Shirt, ShirtVariant


class BagForm(AddToCartForm):
    quantity = forms.IntegerField(initial=1)

    def get_variant(self, clean_data):
        return self.product.variants.get(product__color=self.product.color)


class ShirtForm(AddToCartForm):
    size = forms.ChoiceField(choices=ShirtVariant.SIZE_CHOICES,
                             widget=forms.RadioSelect())
    quantity = forms.IntegerField(initial=1)

    def __init__(self, *args, **kwargs):
        super(ShirtForm, self).__init__(*args, **kwargs)
        available_sizes = [
            (p.size, p.get_size_display()) for p in self.product.variants.all()
        ]
        self.fields['size'].choices = available_sizes

    def get_variant(self, clean_data):
        size = clean_data.get('size')
        return self.product.variants.get(size=size,
                                         product__color=self.product.color)


def get_form_class_for_product(product):
    if isinstance(product, Shirt):
        return ShirtForm
    if isinstance(product, Bag):
        return BagForm
    raise NotImplementedError