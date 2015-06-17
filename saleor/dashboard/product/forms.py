from __future__ import unicode_literals

from django import forms
from django.utils.translation import pgettext_lazy

from ...product.models import (ProductImage, GenericProduct,
                               GenericVariant, Stock, ProductVariant)

PRODUCT_CLASSES = {
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


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['product', 'variant', 'location', 'quantity', 'cost_price']
        widgets = {
            'product': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(StockForm, self).__init__(*args, **kwargs)
        product = self.instance.product
        self.fields['cost_price'].initial = product.price
        if product.has_variants():
            self.fields['variant'].choices = [(variant.pk, variant) for variant
                                              in product.variants.all()]
        else:
            del self.fields['variant']


class GenericProductForm(forms.ModelForm):
    class Meta:
        model = GenericProduct
        exclude = []


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        exclude = []
        widgets = {
            'product': forms.HiddenInput()
        }


class GenericVariantForm(ProductVariantForm):
    class Meta:
        model = GenericVariant
        exclude = ProductVariantForm._meta.exclude
        widgets = ProductVariantForm._meta.widgets


def get_product_form(product):
    if isinstance(product, GenericProduct):
        return GenericProductForm
    else:
        raise ValueError('Unknown product class')


def get_product_cls_by_name(cls_name):
    if cls_name not in PRODUCT_CLASSES:
        raise ValueError('Unknown product class')
    return PRODUCT_CLASSES[cls_name]


def get_variant_form(product):
    if isinstance(product, GenericProduct):
        return GenericVariantForm
    else:
        raise ValueError('Unknown product class')


def get_variant_cls(product):
    if isinstance(product, GenericProduct):
        return GenericVariant
    else:
        raise ValueError('Unknown product class')


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        exclude = ('product', 'order')
