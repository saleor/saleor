from __future__ import unicode_literals

from django import forms
from django.forms.models import inlineformset_factory
from django.forms.widgets import ClearableFileInput
from django.utils.translation import pgettext_lazy

from ...product.models import (ProductImage, Product, ShirtVariant, BagVariant,
                               Shirt, Bag)

PRODUCT_CLASSES = {
    'shirt': Shirt,
    'bag': Bag}


class ProductClassForm(forms.Form):

    product_cls = forms.ChoiceField(
        label=pgettext_lazy('Product class form label', 'Product class'),
        widget=forms.RadioSelect,
        choices=[(name, name.capitalize()) for name in PRODUCT_CLASSES.keys()])


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'collection']


class ShirtForm(ProductForm):
    class Meta:
        model = Shirt
        exclude = []


class BagForm(ProductForm):
    class Meta:
        model = Bag
        exclude = []


class ImageInputWidget(ClearableFileInput):
    url_markup_template = '<a href="{0}"><img src="{0}" width=50 /></a>'


formset_defaults = {
    'extra': 1,
    'min_num': 1,
    'validate_min': True
}


ShirtVariantFormset = inlineformset_factory(
    Shirt, ShirtVariant, exclude=[], **formset_defaults)
BagVariantFormset = inlineformset_factory(
    Bag, BagVariant, exclude=[], **formset_defaults)


def get_product_form(product):
    if isinstance(product, Shirt):
        return ShirtForm
    elif isinstance(product, Bag):
        return BagForm
    else:
        raise ValueError('Unknown product')


def get_product_cls_by_name(cls_name):
    if not cls_name in PRODUCT_CLASSES:
        raise ValueError('Unknown product class')
    return PRODUCT_CLASSES[cls_name]


def get_variant_formset(product):
    if isinstance(product, Shirt):
        return ShirtVariantFormset
    elif isinstance(product, Bag):
        return BagVariantFormset
    else:
        raise ValueError('Unknown product')


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        exclude = ('product', 'order')
