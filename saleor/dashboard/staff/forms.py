from django import forms

from ...userprofile.models import User


class StaffForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.update(initial={'is_staff': True})
        super(StaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['email', 'groups', 'is_staff', 'is_active']
