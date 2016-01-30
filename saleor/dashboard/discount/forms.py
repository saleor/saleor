from django import forms
from django.utils.translation import pgettext_lazy

from ...discount.models import Sale


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        exclude = []
        widgets = {
            'type': forms.RadioSelect()}

    def clean(self):
        cleaned_data = super(SaleForm, self).clean()
        discount_type = cleaned_data['type']
        value = cleaned_data['value']
        if discount_type == Sale.PERCENTAGE and value > 100:
            self.add_error('value', pgettext_lazy(
                'sale error',
                'Sale cannot exceed 100%'))
        return cleaned_data
