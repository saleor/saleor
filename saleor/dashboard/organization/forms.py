from django import forms
from django.utils.translation import pgettext_lazy

from ...account.models import Organization


class OrganizationDeleteForm(forms.Form):

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
                'Edit organization details in order form error',
                'You can\'t delete a organization with associated users.'))
        can_edit_organization = self.user.has_perm('account.manage_organizations')
        if not can_edit_organization:
            raise forms.ValidationError(pgettext_lazy(
                'Edit organization details in order form error',
                'You have insufficient permissions to edit organizations.'))
        return data


class OrganizationForm(forms.ModelForm):

    class Meta:
        model = Organization
        fields = ['name', 'is_active']
