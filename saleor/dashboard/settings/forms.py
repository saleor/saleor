from django import forms
from django.utils.translation import ugettext_lazy as _
from ...setting.models import Setting


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = []

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name.split()) > 1:
            raise forms.ValidationError(_("Name cannot contains whitespaces"))
        return name
