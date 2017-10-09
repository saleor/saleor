from django import forms

from ...userprofile.models import User


class StaffPromoteForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['is_staff']
