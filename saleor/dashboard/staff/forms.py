from django import forms

from ...userprofile.models import User


class StaffForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'groups', 'is_superuser', 'is_staff',
                  'is_active']

    def is_valid(self):
        return self.is_bound and not self.errors
