from django import forms

from ...site.models import SiteSettings


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = []
