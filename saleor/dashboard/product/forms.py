from __future__ import unicode_literals

from django import forms
from django.forms.models import inlineformset_factory
from django.utils.translation import pgettext_lazy

from ...product.models import (ProductImage, Stock, ProductVariant, Product,
                               ProductAttribute, AttributeChoiceValue)

PRODUCT_CLASSES = {
    Product: 'Default'
}


def get_verbose_name(model):
    return model._meta.verbose_name


class ProductClassForm(forms.Form):
    product_cls = forms.ChoiceField(
        label=pgettext_lazy('Product class form label', 'Product class'),
        widget=forms.RadioSelect,
        choices=[(cls.__name__, presentation) for cls, presentation in
                 PRODUCT_CLASSES.iteritems()])

    def __init__(self, *args, **kwargs):
        super(ProductClassForm, self).__init__(*args, **kwargs)
        self.fields['product_cls'].initial = PRODUCT_CLASSES.keys()[0].__name__


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        exclude = []
        widgets = {
            'product': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product')
        super(StockForm, self).__init__(*args, **kwargs)
        variants = product.variants.all()
        if variants:
            self.fields['variant'].choices = [(variant.pk, variant) for variant
                                              in variants]
        else:
            self.fields['variant'].widget.attrs['disabled'] = True


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = pgettext_lazy(
            'Product form labels', 'Give your awesome product a name')
        self.fields['categories'].widget.attrs[
            'data-placeholder'] = pgettext_lazy('Product form labels', 'Search')
        self.fields['attributes'].widget.attrs[
            'data-placeholder'] = pgettext_lazy('Product form labels', 'Search')


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        exclude = ['attributes']
        widgets = {
            'product': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super(ProductVariantForm, self).__init__(*args, **kwargs)
        self.fields['price_override'].widget.attrs[
            'placeholder'] = self.instance.product.price.gross
        self.fields['weight_override'].widget.attrs[
            'placeholder'] = self.instance.product.weight


class VariantAttributesForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = []

    def __init__(self, *args, **kwargs):
        super(VariantAttributesForm, self).__init__(*args, **kwargs)
        self.available_attrs = self.instance.product.attributes.prefetch_related(
            'values').all()
        for attr in self.available_attrs:
            field_defaults = {'label': attr.display, 'required': True,
                              'initial': self.instance.get_attribute(attr.pk)}
            if attr.has_values():
                choices = [('', '')] + [(value.pk, value.display)
                                        for value in attr.values.all()]
                field = forms.ChoiceField(choices=choices, **field_defaults)
            else:
                field = forms.CharField(**field_defaults)
            self.fields[attr.get_formfield_name()] = field

    def save(self, commit=True):
        attributes = {attr.pk: self.cleaned_data.pop(attr.get_formfield_name())
                      for attr in self.available_attrs}
        self.instance.attributes = attributes
        return super(VariantAttributesForm, self).save(commit=commit)


class BulkDeleteForm(forms.Form):
    items = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        model = getattr(self, 'model', None)
        if not model:
            raise ValueError('BulkDeleteForm has no model specified')
        super(BulkDeleteForm, self).__init__(*args, **kwargs)
        self.fields['items'].choices = choices

    def delete(self):
        items = self.model.objects.filter(pk__in=self.cleaned_data['items'])
        items.delete()


class VariantsBulkDeleteForm(BulkDeleteForm):
    model = ProductVariant


class StockBulkDeleteForm(BulkDeleteForm):
    model = Stock


def get_product_form(product):
    if isinstance(product, Product):
        return ProductForm
    else:
        raise ValueError('Unknown product class')


def get_product_cls_by_name(cls_name):
    for cls in PRODUCT_CLASSES.keys():
        if cls_name == cls.__name__:
            return cls
    raise ValueError('Unknown product class')


def get_variant_form(product):
    if isinstance(product, Product):
        return ProductVariantForm
    else:
        raise ValueError('Unknown product class')


def get_variant_cls(product):
    if isinstance(product, Product):
        return ProductVariant
    else:
        raise ValueError('Unknown product class')


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        exclude = ('product', 'order')


class ProductAttributeForm(forms.ModelForm):
    class Meta:
        model = ProductAttribute
        exclude = []


AttributeChoiceValueFormset = inlineformset_factory(
    ProductAttribute, AttributeChoiceValue, exclude=(), extra=1)
