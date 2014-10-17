from django import forms
from django.utils.translation import ugettext_lazy as _


class CustomerSearchForm(forms.Form):
    email = forms.CharField(required=False, label=_('Email'))
    name = forms.CharField(required=False, label=_('Name'))

    def clean(self):
        data = self.cleaned_data
        if not any(data.values()):
            raise forms.ValidationError(
                _('At least one field must be specified'), code='invalid')
        for k in data.keys():
            data[k] = data[k].strip()
        return data
