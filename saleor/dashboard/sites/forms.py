from django import forms
from django.utils.translation import ugettext_lazy as _

from ...site.models import SiteSetting


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        exclude = []

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name.split()) > 1:
            raise forms.ValidationError(_("Name cannot contains whitespaces"))
        return name
