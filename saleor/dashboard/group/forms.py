from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

from ...core.permissions import get_permissions


class GroupPermissionsForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': _('name'),
            'permissions': _('permissions'),
        }

    permissions = forms.ModelMultipleChoiceField(
        queryset=get_permissions(),
        widget=forms.CheckboxSelectMultiple
    )
