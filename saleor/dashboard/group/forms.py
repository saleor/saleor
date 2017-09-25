from django import forms
from django.contrib.auth.models import Group

from ...core.permissions import get_permissions


class GroupPermissionsForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']

    permissions = forms.ModelMultipleChoiceField(
        queryset=get_permissions(),
        widget=forms.CheckboxSelectMultiple
    )
