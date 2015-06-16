from __future__ import unicode_literals

from django import forms
from django.forms.models import inlineformset_factory
from django.forms.widgets import ClearableFileInput
from django.utils.translation import pgettext_lazy

from ...product.models import (ProductImage, Product, GenericProduct,
                               GenericVariant, ShirtVariant, Shirt, Bag,
                               BagVariant)

PRODUCT_CLASSES = {
    'shirt': Shirt,
    'bag': Bag,
    'generic_product': GenericProduct
}

def get_verbose_name(model):
    return model._meta.verbose_name


class ProductClassForm(forms.Form):
    product_cls = forms.ChoiceField(
        label=pgettext_lazy('Product class form label', 'Product class'),
        widget=forms.RadioSelect,
        choices=[(name, get_verbose_name(cls).capitalize()) for name, cls in
                 PRODUCT_CLASSES.iteritems()])

    def __init__(self, *args, **kwargs):
        super(ProductClassForm, self).__init__(*args, **kwargs)
        self.fields['product_cls'].initial = PRODUCT_CLASSES.keys()[0]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'collection']


class GenericProductForm(ProductForm):
    class Meta:
        model = GenericProduct
        exclude = []


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
GenericVariantFormset = inlineformset_factory(
    GenericProduct, GenericVariant, exclude=[], **formset_defaults
)


def get_product_form(product):
    if isinstance(product, GenericProduct):
        return GenericProductForm
    elif isinstance(product, Shirt):
        return ShirtForm
    elif isinstance(product, Bag):
        return BagForm
    else:
        raise ValueError('Unknown product class')


def get_product_cls_by_name(cls_name):
    if cls_name not in PRODUCT_CLASSES:
        raise ValueError('Unknown product class')
    return PRODUCT_CLASSES[cls_name]


def get_variant_formset(product):
    if isinstance(product, Shirt):
        return ShirtVariantFormset
    elif isinstance(product, Bag):
        return BagVariantFormset
    elif isinstance(product, GenericProduct):
        return GenericVariantFormset
    else:
        raise ValueError('Unknown product')


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        exclude = ('product', 'order')
