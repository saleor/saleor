from django import forms
from django.utils.translation import pgettext_lazy

from ...account.models import User
from ...core.permissions import get_permissions


class StaffForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.instance.is_staff = True
        self.fields['user_permissions'].queryset = get_permissions()
        if self.user == self.instance:
            self.fields['is_active'].disabled = True

    class Meta:
        model = User
        fields = ['email', 'user_permissions', 'is_active']
        labels = {
            'email': pgettext_lazy(
                'Email', 'Email'),
            'user_permissions': pgettext_lazy(
                'Label of the dropdown with permissions', 'Permissions'),
            'is_active': pgettext_lazy(
                'User active toggle', 'User is active')}
