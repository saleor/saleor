from django import forms

from ...account.models import Company


class CompanyForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = ['name', 'is_active']
