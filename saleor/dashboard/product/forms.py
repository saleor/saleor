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
        self.fields['name'].widget.attrs['placeholder'] = pgettext_lazy('Product form labels', 'Give your awesome product a name')
        self.fields['categories'].widget.attrs['data-placeholder'] = pgettext_lazy('Product form labels', 'Search')
        self.fields['attributes'].widget.attrs['data-placeholder'] = pgettext_lazy('Product form labels', 'Search')

    def save(self, commit=True):
        old_attrs = [attr.pk for attr in self.instance.attributes.all()]
        product = super(ProductForm, self).save(commit=commit)
        new_attrs = [attr.pk for attr in product.attributes.all()]
        self.update_variant_attributes(old_attrs, new_attrs)
        return product

    def update_variant_attributes(self, old_attrs, new_attrs):
        removed = [attr for attr in old_attrs if attr not in new_attrs]
        if removed:
            for variant in self.instance.variants.all():
                for pk in removed:
                    try:
                        del variant.attributes[str(pk)]
                    except KeyError:
                        pass
                variant.save()


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        exclude = ['attributes']
        widgets = {
            'product': forms.HiddenInput(),
            'attributes': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(ProductVariantForm, self).__init__(*args, **kwargs)
        self.json_fields = []
        self.product_attributes = self.instance.product.attributes.prefetch_related(
            'values').all()
        for attr in self.product_attributes:
            field_defaults = {
                'label': attr.display,
                'required': True
            }
            if self.instance.attributes:
                field_defaults['initial'] = self.instance.attributes.get(attr.pk)
            if attr.has_values():
                choices = [('', '')] + [(value.pk, value.display)
                                        for value in attr.values.all()]
                self.fields[attr.get_formfield_name()] = forms.ChoiceField(
                    choices=choices, **field_defaults)
            else:
                self.fields[attr.get_formfield_name()] = forms.CharField(**field_defaults)

    def save(self, commit=True):
        attributes = {attr.pk: self.cleaned_data.pop(attr.get_formfield_name())
                      for attr in self.product_attributes}
        self.instance.attributes = attributes
        return super(ProductVariantForm, self).save(commit=commit)


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
