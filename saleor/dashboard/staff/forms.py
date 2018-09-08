from django import forms
from django.utils.translation import pgettext_lazy

from ...account.models import User
from ...core.permissions import get_permissions
from ..forms import PermissionMultipleChoiceField


class StaffForm(forms.ModelForm):
    user_permissions = PermissionMultipleChoiceField(
        queryset=get_permissions(),
        widget=forms.CheckboxSelectMultiple, required=False,
        label=pgettext_lazy(
            'Label above the permissions choicefield', 'Permissions'))

    class Meta:
        model = User
        fields = ['email', 'user_permissions', 'is_active']
        labels = {
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
