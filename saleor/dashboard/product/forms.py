from django import forms
from django.forms.models import inlineformset_factory
from django.forms.widgets import ClearableFileInput

from ...product.models import (ProductImage, Product, ShirtVariant, BagVariant,
                               Shirt, Bag)


PRODUCT_CLASSES = {
    'shirt': Shirt,
    'bag': Bag
}


class ProductClassForm(forms.Form):
    cls_name = forms.ChoiceField(
        choices=[(name, name.capitalize()) for name in PRODUCT_CLASSES.keys()])


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'collection']


class ShirtForm(ProductForm):
    class Meta:
        model = Shirt


class BagForm(ProductForm):
    class Meta:
        model = Bag


class ImageInputWidget(ClearableFileInput):
    url_markup_template = '<a href="{0}"><img src="{0}" width=50 /></a>'


ProductImageFormSet = inlineformset_factory(Product, ProductImage, extra=1,
                                            widgets={'image': ImageInputWidget})
ShirtVariantFormset = inlineformset_factory(Shirt, ShirtVariant, extra=1)
BagVariantFormset = inlineformset_factory(Bag, BagVariant, extra=1)


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
