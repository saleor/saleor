from django import forms

from ...userprofile.models import User


class StaffForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        kwargs.update(initial={'is_staff': True})
        super(StaffForm, self).__init__(*args, **kwargs)
        if self.user == self.instance:
            self.fields['is_staff'].disabled = True
            self.fields['is_active'].disabled = True

    class Meta:
        model = User
        fields = ['email', 'groups', 'is_staff', 'is_active']
