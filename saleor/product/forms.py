from django import forms

from ..cart.forms import AddToCartForm
from .models import Bag, Shirt


class BagForm(AddToCartForm):

    color = forms.CharField()


class ShirtForm(AddToCartForm):

    color = forms.CharField()


def get_form_class_for_product(product):
    if type(product) is Shirt:
        return ShirtForm
    if type(product) is Bag:
        return BagForm
    raise NotImplemented()