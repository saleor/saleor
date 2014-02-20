from django import forms

from ..cart.forms import AddToCartForm
from .models import Bag, BagVariant, Shirt, ShirtVariant, Color


class BagForm(AddToCartForm):
    quantity = forms.IntegerField(initial=1)

    def get_variant(self, clean_data):
        return BagVariant.objects.get(product__color=self.product.color)


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
        return ShirtVariant.objects.get(size=size,
                                        product__color=self.product.color)


def get_form_class_for_product(product):
    if type(product) is Shirt:
        return ShirtForm
    if type(product) is Bag:
        return BagForm
    raise NotImplemented()