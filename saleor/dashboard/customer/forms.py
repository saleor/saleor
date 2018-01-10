from django import forms

from ...userprofile.models import User


class CustomerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # disable 'is_active' checkbox if user edits his own account
        if self.user == self.instance:
            self.fields['is_active'].disabled = True

    class Meta:
        model = User
        fields = ['email', 'is_active']
