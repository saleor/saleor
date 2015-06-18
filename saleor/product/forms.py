from django import forms
from django.utils.translation import pgettext_lazy

from ..cart.forms import AddToCartForm
from ..product.models import GenericProduct


class GenericProductForm(AddToCartForm):
    variant = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(GenericProductForm, self).__init__(*args, **kwargs)
        variants = self.product.variants.all()
        if self.product.has_variants():
            variants = variants.exclude(pk=self.product.base_variant.pk)
        variant_choices = [(v.pk, v) for v in variants]
        self.fields['variant'].choices = variant_choices

    def get_variant(self, cleaned_data):
        pk = cleaned_data['variant']
        return self.product.variants.get(pk=pk)


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
