from django import forms
from django.utils.translation import ugettext_lazy as _


class CustomerSearchForm(forms.Form):
    email = forms.CharField(required=False, label=_('Email'))
    name = forms.CharField(required=False, label=_('Name'))
