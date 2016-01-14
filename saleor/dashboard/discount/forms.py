from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.translation import pgettext_lazy

from ...product.models import Discount


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        exclude = []

    def clean(self):
        cleaned_data = super(DiscountForm, self).clean()
        discount_type = cleaned_data['type']
        apply_on = cleaned_data['apply_on']
        value = cleaned_data['value']
        required_msg = pgettext_lazy('discount error', 'This field is required')
        if discount_type == Discount.PERCENTAGE and value > 100:
            self.add_error('value', pgettext_lazy('discount error',
                                                  'Percentage discount '
                                                  'cannot be higher than 100%'))
        if (apply_on == Discount.APPLY_ON_PRODUCTS and not
                cleaned_data['products']):
            self.add_error('products', required_msg)
        elif (apply_on == Discount.APPLY_ON_CATEGORIES and not
                cleaned_data['categories']):
            self.add_error('categories', required_msg)
        elif apply_on == Discount.APPLY_ON_BOTH and not (
                cleaned_data['products'] or cleaned_data['categories']):
            self.add_error('products', required_msg)
            self.add_error('categories', required_msg)
        # TODO: Implement cost price checks
        return cleaned_data
