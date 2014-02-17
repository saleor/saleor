from django import forms

from ..cart.forms import AddToCartForm
from .models import Bag, BagVariant, Shirt, ShirtVariant, Color


class BagForm(AddToCartForm):

    color = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super(BagForm, self).__init__(*args, **kwargs)
        color_field = self.fields['color']
        color_field.queryset = self.product.get_available_colors()

    def get_variant(self, clean_data):
        color = clean_data.get('color')
        return BagVariant.objects.get(color=color)


class ShirtForm(AddToCartForm):

    color = forms.ModelChoiceField(queryset=None)
    size = forms.ChoiceField(choices=ShirtVariant.SIZE_CHOICES)

    def get_variant(self, clean_data):
        color = clean_data.get('color')
        size = clean_data.get('size')
        return ShirtVariant.objects.get(size=size, color=color)

    def __init__(self, *args, **kwargs):
        super(ShirtForm, self).__init__(*args, **kwargs)
        color_field = self.fields['color']
        color_field.queryset = self.product.get_available_colors()


def get_form_class_for_product(product):
    if type(product) is Shirt:
        return ShirtForm
    if type(product) is Bag:
        return BagForm
    raise NotImplemented()