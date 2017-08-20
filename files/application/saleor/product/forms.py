from __future__ import unicode_literals

import json

from django import forms
from django.utils.encoding import smart_text
from django.utils.translation import pgettext_lazy
from django_prices.templatetags.prices_i18n import gross

from ..cart.forms import AddToCartForm


class VariantChoiceField(forms.ModelChoiceField):
    discounts = None

    def label_from_instance(self, obj):
        variant_label = smart_text(obj)
        label = pgettext_lazy(
            'Variant choice field label',
            '%(variant_label)s - %(price)s') % {
                'variant_label': variant_label,
                'price': gross(obj.get_price(discounts=self.discounts))}
        return label


class ProductForm(AddToCartForm):
    variant = VariantChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        variant_field = self.fields['variant']
        variant_field.queryset = self.product.variants
        variant_field.discounts = self.cart.discounts
        variant_field.empty_label = None
        images_map = {variant.pk: [vi.image.image.url
                                   for vi in variant.variant_images.all()]
                      for variant in self.product.variants.all()}
        variant_field.widget.attrs['data-images'] = json.dumps(images_map)

    def get_variant(self, cleaned_data):
        return cleaned_data.get('variant')

