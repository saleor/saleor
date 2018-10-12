from django import forms
from django.utils.translation import pgettext_lazy

from ...account.models import User
from ...core.permissions import get_permissions
from ..forms import PermissionMultipleChoiceField


def get_name_placeholder(name):
    return pgettext_lazy(
        'Customer form: Name field placeholder',
        '%(name)s (Inherit from default biling address)') % {
            'name': name}


class StaffForm(forms.ModelForm):
    user_permissions = PermissionMultipleChoiceField(
        queryset=get_permissions(),
        widget=forms.CheckboxSelectMultiple, required=False,
        label=pgettext_lazy(
            'Label above the permissions choicefield', 'Permissions'))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email',
                  'user_permissions', 'is_active']
        labels = {
            'first_name': pgettext_lazy(
                'Customer form: Given name field', 'Given name'),
            'last_name': pgettext_lazy(
                'Customer form: Family name field', 'Family name'),
            'email': pgettext_lazy(
                'Email', 'Email'),
            'is_active': pgettext_lazy(
                'User active toggle', 'User is active')}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.instance.is_staff = True
        if self.user == self.instance:
            self.fields['is_active'].disabled = True

        address = self.instance.default_billing_address
        if not address:
            return
        if address.first_name:
            placeholder = get_name_placeholder(address.first_name)
            self.fields['first_name'].widget.attrs['placeholder'] = placeholder
        if address.last_name:
            placeholder = get_name_placeholder(address.last_name)
            self.fields['last_name'].widget.attrs['placeholder'] = placeholder
