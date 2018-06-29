from django import forms
from django.utils.translation import pgettext_lazy

from ...account.models import Company


class CompanyDeleteForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if not self.user.is_staff:
            return data

        if self.user.company == self.user:
            raise forms.ValidationError(pgettext_lazy(
                'Edit company details in order form error',
                'You can\'t delete your own company via dashboard, '
                'please try from the storefront.'))
        can_edit_company = self.user.has_perm('account.edit_company')
        if not can_edit_company:
            raise forms.ValidationError(pgettext_lazy(
                'Edit company details in order form error',
                'You have insufficient permissions to edit companies.'))
        return data


class CompanyForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = ['name', 'is_active']
