from django import forms
from django.utils.translation import pgettext_lazy

from ...userprofile.models import User


class StaffForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.instance.is_staff = True
        if self.user == self.instance:
            self.fields['is_active'].disabled = True

    class Meta:
        model = User
        fields = ['email', 'groups', 'is_active']
        labels = {
            'email': pgettext_lazy(
                'Email', 'Email'),
            'groups': pgettext_lazy(
                'Groups', 'Groups'),
            'is_active': pgettext_lazy(
                'User active toggle', 'User is active')}
