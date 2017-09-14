from django import forms
from django.contrib.admin import widgets

from ...userprofile.models import User


class UserGroupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['groups']
        widgets = {
            "groups": widgets.FilteredSelectMultiple(('groups'), False)
        }
