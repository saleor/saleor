import json

from django import forms
from django.forms import ChoiceField
from django.forms.models import ModelChoiceIterator
from django.template.loader import render_to_string
from django.utils.translation import pgettext_lazy
from django_prices.templatetags.prices_i18n import gross

from ..cart.forms import AddToCartForm


class VariantChoiceIterator(ModelChoiceIterator):
    product_instance = None

    def __init__(self, field):
        super(VariantChoiceIterator, self).__init__(field)
        self.product = self.product_instance
        self.attributes = self.product.attributes if self.product else None

    def choice(self, obj):
        label = obj.display_variant(self.attributes)
        label += ' - ' + gross(obj.get_price())
        return (self.field.prepare_value(obj), label)


class VariantChoiceField(forms.ModelChoiceField):
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return VariantChoiceIterator(self)
    choices = property(_get_choices, ChoiceField._set_choices)


class ProductForm(AddToCartForm):
    variant = VariantChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        variant_field = self.fields['variant']
        variant_field.product_instance = self.product
        variant_field.queryset = self.product.variants
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
