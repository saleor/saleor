from django import forms
from django.forms.models import inlineformset_factory
from ...product.models import (ProductImage, Product, Category, ShirtVariant,
                               BagVariant, Shirt, Bag)


class ProductCategory(forms.Form):
    category = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(ProductCategory, self).__init__(*args, **kwargs)
        categories = Category.objects.all()
        self.fields['category'].choices = [(c.slug, c.name) for c in categories]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['category']
        fields = ['name', 'description', 'collection']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)


class ShirtForm(ProductForm):
    class Meta:
        model = Shirt


class BagForm(ProductForm):
    class Meta:
        model = Bag


ProductImageFormSet = inlineformset_factory(Product, ProductImage, extra=0)
ShirtVariantFormset = inlineformset_factory(Shirt, ShirtVariant, extra=0)
BagVariantFormset = inlineformset_factory(Bag, BagVariant, extra=0)


def get_product_form_class(product):
    if isinstance(product, Shirt):
        return ShirtForm
    elif isinstance(product, Bag):
        return BagForm
    else:
        return ProductForm


def get_variant_formset_class(product):
    if isinstance(product, Shirt):
        return ShirtVariantFormset
    elif isinstance(product, Bag):
        return BagVariantFormset
    else:
        raise ValueError('Unknown product')
