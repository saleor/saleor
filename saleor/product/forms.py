from __future__ import unicode_literals

import json

from django import forms
from django.template.loader import render_to_string
from django.utils.translation import pgettext_lazy
from django_prices.templatetags.prices_i18n import gross

from ..cart.forms import AddToCartForm


class VariantChoiceField(forms.ModelChoiceField):
    discounts = None

    def label_from_instance(self, obj):
        attributes = obj.product.product_class.variant_attributes.all()
        variant_label = obj.display_variant(attributes)
        label = '%(variant_label)s - %(price)s' % {
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


class ProductVariantInline(forms.models.BaseInlineFormSet):
    error_no_items = pgettext_lazy(
        'Product admin error', 'You have to create at least one variant')

    def clean(self):
        count = 0
        for form in self.forms:
            if form.cleaned_data:
                count += 1
        if count < 1:
            raise forms.ValidationError(self.error_no_items)


class ImageInline(ProductVariantInline):
    error_no_items = pgettext_lazy(
        'Product admin error', 'You have to add at least one image')


def get_form_class_for_product(product):
    from ..product.models import Product
    if isinstance(product, Product):
        return ProductForm
    raise NotImplementedError


class WeightInput(forms.TextInput):
    template = 'weight_field_widget.html'

    def __init__(self, unit, *args, **kwargs):
        self.unit = unit
        super(WeightInput, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        widget = super(WeightInput, self).render(name, value, attrs=attrs)
        return render_to_string(self.template, {'widget': widget,
                                                'value': value,
                                                'unit': self.unit})


class WeightField(forms.DecimalField):
    def __init__(self, unit, decimal_places, widget=WeightInput, *args,
                 **kwargs):
        self.unit = unit
        step = 10 ** -decimal_places
        if isinstance(widget, type):
            widget = widget(unit=self.unit,
                            attrs={'type': 'number', 'step': step})
        super(WeightField, self).__init__(*args, widget=widget, **kwargs)
