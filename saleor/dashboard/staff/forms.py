from django import forms
from django.utils.translation import pgettext_lazy

from ...account.models import User
from ...core.permissions import get_permissions
from ..customer.forms import get_name_placeholder
from ..forms import PermissionMultipleChoiceField


class StaffForm(forms.ModelForm):
    user_permissions = PermissionMultipleChoiceField(
        queryset=get_permissions(),
        widget=forms.CheckboxSelectMultiple, required=False,
        label=pgettext_lazy(
            'Label above the permissions choicefield', 'Permissions'))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email',
                  'user_permissions', 'is_active', 'is_staff', 'is_superuser']
        labels = {
            'first_name': pgettext_lazy(
                'Customer form: Given name field', 'Given name'),
            'last_name': pgettext_lazy(
                'Customer form: Family name field', 'Family name'),
            'email': pgettext_lazy(
                'Email', 'Email'),
            'is_active': pgettext_lazy(
                'User active toggle', 'User is active'),
            'is_staff': pgettext_lazy(
                'User staff toggle', 'User is staff'),
            'is_superuser': pgettext_lazy(
                'User superuser toggle', 'User is superuser')}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Expose superuser field but disable it
        self.fields['is_superuser'].disabled = True

        # Disable users editing their own following fields
        if self.user == self.instance:
            self.fields['is_active'].disabled = True
            self.fields['is_staff'].disabled = True

        # Non-superuser couldn't edit superuser's profile
        if (self.user and not self.user.is_superuser
                and self.instance.is_superuser):
            self.fields['email'].disabled = True
            self.fields['user_permissions'].disabled = True
            self.fields['is_active'].disabled = True
            self.fields['is_staff'].disabled = True

        address = self.instance.default_billing_address
        if not address:
            return
        if address.first_name:
            placeholder = get_name_placeholder(address.first_name)
            self.fields['first_name'].widget.attrs['placeholder'] = placeholder
        if address.last_name:
            placeholder = get_name_placeholder(address.last_name)
            self.fields['last_name'].widget.attrs['placeholder'] = placeholder

    def clean(self):
        cleaned_data = super().clean()

        # Remove all permissions if user is not staff
        if not cleaned_data['is_staff']:
            cleaned_data['user_permissions'] = []

        return cleaned_data
