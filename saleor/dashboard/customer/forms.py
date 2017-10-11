from django import forms

from ...userprofile.models import User


class StaffPromoteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.admin = kwargs.pop('admin', None)
        super(StaffPromoteForm, self).__init__(*args, **kwargs)
        if self.admin == self.instance or not self.admin.is_superuser:
            self.fields['is_staff'].widget.attrs['disabled'] = True

    class Meta:
        model = User
        fields = ['is_staff']
