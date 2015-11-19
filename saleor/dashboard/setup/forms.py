from __future__ import unicode_literals

from django import forms
from django.contrib.sites.models import Site
from django.utils.translation import pgettext, ugettext_lazy as _

from ...userprofile.models import User


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['domain', 'name']

    def __init__(self, *args, **kwargs):
        current_domain = kwargs.pop('current_domain', None)
        super(SiteForm, self).__init__(*args, **kwargs)
        if current_domain and self.initial.get('domain') != current_domain:
            self.fields['domain'].help_text = pgettext(
                'setup', 'You may want to set this to "%s".') % (current_domain,)


class CreateAdminForm(forms.Form):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    email = forms.EmailField(
        label=_('E-mail'),
        help_text=_('This will be your administrator account.'))
    password1 = forms.CharField(
        label=_('Password'), widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_('Password confirmation'), widget=forms.PasswordInput,
        help_text=_('Enter the same password as above, for verification.'))

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self):
        return User.objects.create_superuser(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'])
