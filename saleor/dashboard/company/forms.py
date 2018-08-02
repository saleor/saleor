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

        if self.instance and self.instance.user_set.exists():
            raise forms.ValidationError(pgettext_lazy(
                'Edit company details in order form error',
                'You can\'t delete a company with associated users.'))
        can_edit_company = self.user.has_perm('account.manage_companies')
        if not can_edit_company:
            raise forms.ValidationError(pgettext_lazy(
                'Edit company details in order form error',
                'You have insufficient permissions to edit companies.'))
        return data


class CompanyForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = ['name', 'is_active']
