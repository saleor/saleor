from django import forms
from django.utils.translation import pgettext_lazy

from ...product.models import Discount


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        exclude = []
        widgets = {
            'type': forms.RadioSelect()}

    def clean(self):
        cleaned_data = super(DiscountForm, self).clean()
        discount_type = cleaned_data['type']
        value = cleaned_data['value']
        if discount_type == Discount.PERCENTAGE and value > 100:
            self.add_error('value', pgettext_lazy(
                'discount error',
                'Discount cannot exceed 100%'))
        return cleaned_data
