from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import pgettext_lazy

from ...core.permissions import get_permissions


class GroupPermissionsForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': pgettext_lazy('Group permission form label', 'Name'),
            'permissions': pgettext_lazy(
                'Group permission form label', 'Permission')}

    permissions = forms.ModelMultipleChoiceField(
        queryset=get_permissions(),
        widget=forms.CheckboxSelectMultiple
    )
