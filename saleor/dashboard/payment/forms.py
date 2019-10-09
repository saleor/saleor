from typing import Dict

from django import forms
from django.utils.text import slugify

from ...extensions import ConfigurationTypeField
from ...extensions.models import PluginConfiguration
from ..forms import ConfigBooleanField, ConfigCharField

TYPE_TO_FIELD = {
    ConfigurationTypeField.STRING: ConfigCharField,
    ConfigurationTypeField.BOOLEAN: ConfigBooleanField,
}


def create_custom_form_field(structure: Dict[str, str]) -> forms.Field:
    elem_type = structure["type"]
    return TYPE_TO_FIELD[elem_type](structure=structure)


class GatewayConfigurationForm(forms.ModelForm):
    class Meta:
        model = PluginConfiguration
        fields = ("active",)

    def __init__(self, plugin, *args, **kwargs):
        self.plugin = plugin
        kwargs["instance"] = self._get_current_configuration()
        super().__init__(*args, **kwargs)
        # add new fields specified for gateway
        self._prepare_fields_for_given_config(self.instance)

    def _get_current_configuration(self) -> PluginConfiguration:
        qs = PluginConfiguration.objects.all()
        return self.plugin.get_plugin_configuration(qs)

    def _prepare_fields_for_given_config(
        self, current_configuration: PluginConfiguration
    ) -> Dict[str, forms.Field]:
        parsed_fields = {}
        structure = current_configuration.configuration
        if structure is None:
            return {}
        for elem in structure:
            slug = slugify(elem["name"])
            self.fields[slug] = create_custom_form_field(elem)
        return parsed_fields

    def parse_values(self):
        cleaned_data = self.cleaned_data
        active = cleaned_data.pop("active", False)
        data = {"active": active}
        data["configuration"] = list(cleaned_data.values())
        return data

    def save(self, *args):
        parse_value = self.parse_values()
        self.plugin.save_plugin_configuration(self.instance, parse_value)
