from django import forms
from django.utils.translation import pgettext_lazy

from ..cart.forms import AddToCartForm
from ..product.models import GenericProduct


class GenericProductForm(AddToCartForm):
    base_variant = forms.CharField(widget=forms.HiddenInput())
    variant = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(GenericProductForm, self).__init__(*args, **kwargs)
        self.fields['base_variant'].initial = self.product.base_variant.pk

        variants = self.product.variants.all().exclude(
            pk=self.product.base_variant.pk)
        self.fields['variant'].choices = [(v.pk, v) for v in variants]
        if not self.product.has_variants():
            self.fields['variant'].widget = forms.HiddenInput()

    def get_variant(self, cleaned_data):
        pk = cleaned_data.get('variant') or cleaned_data.get('base_variant')
        variant = self.product.variants.get(pk=pk)
        return variant


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
    if isinstance(product, GenericProduct):
        return GenericProductForm
    raise NotImplementedError
