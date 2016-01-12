from django import forms
from django.utils.translation import pgettext_lazy

from ...product.models import Discount


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['name', 'type', 'products', 'categories', 'value']

    def clean(self):
        cleaned_data = super(DiscountForm, self).clean()
        type = cleaned_data['type']
        value = cleaned_data['value']
        if type == Discount.PERCENTAGE and value > 100:
            self.add_error('value', pgettext_lazy('discount error',
                                                  'Percentage discount '
                                                  'cannot be higher than 100%'))
        # TODO: Implement cost price checks
        return cleaned_data
