from django import forms

from ...userprofile.models import User


class StaffForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.admin = kwargs.pop('admin', None)
        kwargs.update(initial={'is_staff': True})
        super(StaffForm, self).__init__(*args, **kwargs)
        if self.admin == self.instance:
            self.fields['is_superuser'].widget.attrs['disabled'] = True

    class Meta:
        model = User
        fields = ['email', 'groups', 'is_superuser', 'is_staff',
                  'is_active']
