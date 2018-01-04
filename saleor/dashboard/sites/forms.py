from django import forms
from django.contrib.sites.models import Site
from django.utils.translation import pgettext_lazy

from ...site.models import SiteSettings, AuthorizationKey


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        exclude = []
        labels = {
            'domain': pgettext_lazy(
                'Site form label', 'Domain name'),
            'name': pgettext_lazy(
                'Site form label', 'Display name')}


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = ['site']
        labels = {
            'header_text': pgettext_lazy(
                'Site settings form label', 'Header text'),
            'description': pgettext_lazy(
                'Site settings form label', 'Site description')}


class AuthorizationKeyForm(forms.ModelForm):
    class Meta:
        model = AuthorizationKey
        exclude = []
        labels = {
            'site_settings': pgettext_lazy(
                'Authorization key form label form label', 'Site settings'),
            'key': pgettext_lazy(
                'Authorization key form label form label', 'Key'),
            'password': pgettext_lazy(
                'Authorization key form label form label', 'Password'),
            'name': pgettext_lazy(
                'Authorization key form label form label', 'Name')}
        widgets = {'password': forms.PasswordInput(render_value=True),
                   'key': forms.TextInput(),
                   'site_settings': forms.widgets.HiddenInput()}
