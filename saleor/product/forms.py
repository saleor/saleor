from django import forms
from django.utils.translation import pgettext_lazy
from selectable.forms import AutoCompleteWidget

from ..cart.forms import AddToCartForm
from .models import Bag, Shirt, ShirtVariant
from .lookups import CollectionLookup


class BagForm(AddToCartForm):

    def get_variant(self, clean_data):
        return self.product.variants.get(product__color=self.product.color)


class ShirtForm(AddToCartForm):

    size = forms.ChoiceField(choices=ShirtVariant.SIZE_CHOICES,
                             widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        super(ShirtForm, self).__init__(*args, **kwargs)
        available_sizes = [
            (p.size, p.get_size_display()) for p in self.product.variants.all()]
        self.fields['size'].choices = available_sizes

    def get_variant(self, clean_data):
        size = clean_data.get('size')
        return self.product.variants.get(size=size,
                                         product__color=self.product.color)


class ShirtAdminForm(forms.ModelForm):
    class Meta:
        model = Shirt
        exclude = []
        widgets = {
            'collection': AutoCompleteWidget(CollectionLookup)}


class ProductVariantInline(forms.models.BaseInlineFormSet):
    error_no_items = pgettext_lazy('Product admin error', 'You have to create at least one variant')

    def clean(self):
        count = 0
        for form in self.forms:
            if form.cleaned_data:
                count += 1
        if count < 1:
            raise forms.ValidationError(self.error_no_items)


class ImageInline(ProductVariantInline):
    error_no_items = pgettext_lazy('Product admin error', 'You have to add at least one image')


def get_form_class_for_product(product):
    if isinstance(product, Shirt):
        return ShirtForm
    if isinstance(product, Bag):
        return BagForm
    raise NotImplementedError
