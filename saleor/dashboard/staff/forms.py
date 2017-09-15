from django import forms

from ...userprofile.models import User


class UserGroupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['groups']
