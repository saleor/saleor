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
                'Domain name', 'Domain name'),
            'name': pgettext_lazy(
                'Display name', 'Display name')}


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = ['site']
        labels = {
            'header_text': pgettext_lazy(
                'Header text', 'Header text'),
            'description': pgettext_lazy(
                'Site description', 'Description')}


class AuthorizationKeyForm(forms.ModelForm):
    class Meta:
        model = AuthorizationKey
        exclude = []
        labels = {
            'site_settings': pgettext_lazy(
                'Site settings', 'Settings'),
            'key': pgettext_lazy(
                'Key', 'Key'),
            'password': pgettext_lazy(
                'Password', 'Password'),
            'name': pgettext_lazy(
                'Authorization key name', 'Name')}
        widgets = {'password': forms.PasswordInput(render_value=True),
                   'key': forms.TextInput(),
                   'site_settings': forms.widgets.HiddenInput()}
