from django import forms
from django.utils.translation import pgettext_lazy

from ...userprofile.models import User


class StaffForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        kwargs.update(initial={'is_staff': True})
        super().__init__(*args, **kwargs)
        if self.user == self.instance:
            self.fields['is_staff'].disabled = True
            self.fields['is_active'].disabled = True

    class Meta:
        model = User
        fields = ['email', 'groups', 'is_staff', 'is_active']
        labels = {
            'email': pgettext_lazy(
                'Staff form label', 'Email'),
            'groups': pgettext_lazy(
                'Staff form label', 'Groups'),
            'is_active': pgettext_lazy(
                'Staff form label', 'Active'),
            'is_staff': pgettext_lazy(
                'Staff form label', 'Staff')}

