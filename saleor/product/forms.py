from django import forms
from django.template.loader import render_to_string
from django.utils.translation import pgettext_lazy

from ..cart.forms import AddToCartForm


class ProductForm(AddToCartForm):
    variant = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        variants = self.product.variants.all()
        self.fields['variant'].choices = [(v.pk, v) for v in variants]

    def get_variant(self, cleaned_data):
        pk = cleaned_data.get('variant')
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

    def __init__(self, unit, widget=WeightInput, *args, **kwargs):
        self.unit = unit
        if isinstance(widget, type):
            widget = widget(unit=self.unit, attrs={'type': 'number'})
        super(WeightField, self).__init__(*args, widget=widget, **kwargs)
