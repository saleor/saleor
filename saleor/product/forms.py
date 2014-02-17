from django import forms

from ..cart.forms import AddToCartForm
from .models import Bag, BagVariant, Shirt, ShirtVariant


class BagForm(AddToCartForm):

    color = forms.ChoiceField(choices=BagVariant.COLOR_CHOICES)

    def __init__(self, *args, **kwargs):
        super(BagForm, self).__init__(*args, **kwargs)
        color_field = self.fields['color']
        color_values = list(
            self.product.variants.values_list('color', flat=True))
        color_choices = color_field.choices
        new_choices = [
            choice for choice in color_choices if choice[0] in color_values]
        color_field.choices = new_choices

    def get_variant(self, clean_data):
        color = clean_data.get('color')
        return BagVariant.objects.get(color=color)


class ShirtForm(AddToCartForm):

    color = forms.ChoiceField(choices=ShirtVariant.COLOR_CHOICES)
    size = forms.ChoiceField(choices=ShirtVariant.SIZE_CHOICES)

    def get_variant(self, clean_data):
        color = clean_data.get('color')
        size = clean_data.get('size')
        return ShirtVariant.objects.get(color=color, size=size)


def get_form_class_for_product(product):
    if type(product) is Shirt:
        return ShirtForm
    if type(product) is Bag:
        return BagForm
    raise NotImplemented()