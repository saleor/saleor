from django import forms

from ...userprofile.models import User


class StaffForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.admin = kwargs.pop('admin', '1')
        super(StaffForm, self).__init__(*args, **kwargs)
        if self.admin == self.instance:
            self.fields['is_superuser'].widget.attrs['disabled'] = True

    class Meta:
        model = User
        fields = ['email', 'groups', 'is_superuser', 'is_staff',
                  'is_active']

    def is_valid(self):
        return self.is_bound and not self.errors
