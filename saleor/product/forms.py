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

    def update_field_data(self, variants, cart):
        """Initialize variant picker metadata."""
        self.queryset = variants
        self.discounts = cart.discounts
        self.empty_label = None
        images_map = {
            variant.pk: [
                vi.image.image.url for vi in variant.variant_images.all()]
            for variant in variants.all()}
        self.widget.attrs['data-images'] = json.dumps(images_map)
        # Don't display select input if there are less than two variants
        if self.queryset.count() < 2:
            self.widget = forms.HiddenInput(
                {'value': variants.all()[0].pk})


class ProductForm(AddToCartForm):
    variant = VariantChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        variant_field = self.fields['variant']
        variant_field.update_field_data(self.product.variants, self.cart)

    def get_variant(self, cleaned_data):
        return cleaned_data.get('variant')
