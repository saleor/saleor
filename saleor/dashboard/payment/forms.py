from typing import Dict

from django import forms
from django.utils.text import slugify

from ...extensions import ConfigurationTypeField
from ...extensions.models import PluginConfiguration
from ..forms import ConfigBooleanField, ConfigCharField, ConfigPasswordField

TYPE_TO_FIELD = {
    ConfigurationTypeField.STRING: ConfigCharField,
    ConfigurationTypeField.BOOLEAN: ConfigBooleanField,
    ConfigurationTypeField.SECRET: ConfigPasswordField,
    ConfigurationTypeField.PASSWORD: ConfigPasswordField,
}


def create_custom_form_field(structure: Dict[str, str]) -> forms.Field:
    elem_type = structure["type"]
    elem_name = structure["name"]
    elem_value = structure["value"]
    elem_help_text = structure["help_text"]
    return TYPE_TO_FIELD[elem_type](
        initial=elem_value, help_text=elem_help_text, label=elem_name
    )


class GatewayConfigurationForm(forms.ModelForm):
    class Meta:
        model = PluginConfiguration
        fields = ("active",)

    def __init__(self, plugin, *args, **kwargs):
        self.plugin = plugin
        kwargs["instance"] = self._get_or_create_db_configuration()
        super().__init__(*args, **kwargs)
        # add new fields specified for gateway
        self._prepare_fields_for_given_config()

    def _get_or_create_db_configuration(self) -> PluginConfiguration:
        defaults = self.plugin._get_default_configuration()
        return PluginConfiguration.objects.get_or_create(
            name=self.plugin.PLUGIN_NAME, defaults=defaults
        )[0]

    def _prepare_fields_for_given_config(self) -> Dict[str, forms.Field]:
        qs = PluginConfiguration.objects.all()
        configuration = self.plugin.get_plugin_configuration(qs).configuration
        parsed_fields = {}
        if configuration is None:
            return {}
        for elem in configuration:
            name = elem["name"]
            slug = slugify(name)
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
