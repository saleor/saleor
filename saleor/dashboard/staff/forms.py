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
                'Email', 'Email'),
            'groups': pgettext_lazy(
                'Groups', 'Groups'),
            'is_active': pgettext_lazy(
                'User active toggle', 'User is active'),
            'is_staff': pgettext_lazy(
                'User dashboard access toggle', 'Has access to dashboard')}
