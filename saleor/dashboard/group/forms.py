from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import pgettext_lazy

from ...core.permissions import get_permissions
from ..forms import PermissionMultipleChoiceField


class GroupPermissionsForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': pgettext_lazy('Item name', 'Name'),
            'permissions': pgettext_lazy('Permissions', 'Permissions')}

    permissions = PermissionMultipleChoiceField(
        queryset=get_permissions(),
        widget=forms.CheckboxSelectMultiple)
