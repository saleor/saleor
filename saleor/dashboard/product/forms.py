from django import forms
from django.forms.models import inlineformset_factory
from ...product.models import (ProductImage, Product, Category, ShirtVariant,
                               BagVariant, Shirt, Bag)


class ProductCategoryForm(forms.Form):
    category = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(ProductCategoryForm, self).__init__(*args, **kwargs)
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
        exclude = ProductForm.Meta.exclude


class BagForm(ProductForm):
    class Meta:
        model = Bag
        exclude = ProductForm.Meta.exclude


ProductImageFormSet = inlineformset_factory(Product, ProductImage, extra=1)
ShirtVariantFormset = inlineformset_factory(Shirt, ShirtVariant, extra=1)
BagVariantFormset = inlineformset_factory(Bag, BagVariant, extra=1)


def get_product_form(product, category=None):
    if product:
        if isinstance(product, Shirt):
            return ShirtForm
        elif isinstance(product, Bag):
            return BagForm
        else:
            return ProductForm
    elif category:
        if category == 'shirts':
            return ShirtForm
        elif category == 'grocery-bags':
            return BagForm
        else:
            return ValueError('Unknown category')
    else:
        raise ValueError('No product and category were given')


def get_variant_formset(product, category=None):
    if product:
        if isinstance(product, Shirt):
            return ShirtVariantFormset
        elif isinstance(product, Bag):
            return BagVariantFormset
        else:
            raise ValueError('Unknown product')
    elif category:
        if category == 'shirts':
            return ShirtVariantFormset
        elif category == 'grocery-bags':
            return BagVariantFormset
        else:
            raise ValueError('Unknown category')
    else:
        raise ValueError('No product and category were given')
