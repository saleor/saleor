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


class GatewayConfigurationForm(forms.Form):
    active = forms.BooleanField()

    def __init__(self, plugin, *args, **kwargs):
        self.plugin = plugin
        super().__init__(*args, **kwargs)
        self.current_configuration = self._get_current_configuration()
        # add new fields specified for gateway
        self.fields.update(
            self._prepare_fields_for_given_config(self.current_configuration)
        )
        self.fields["active"].initial = self.current_configuration.active

    def _get_current_configuration(self) -> PluginConfiguration:
        qs = PluginConfiguration.objects.all()
        return self.plugin.get_plugin_configuration(qs)

    def _create_field(self, structure: Dict[str, str]) -> forms.Field:
        elem_type = structure["type"]
        return TYPE_TO_FIELD[elem_type](structure=structure)

    def _prepare_fields_for_given_config(
        self, current_configuration: PluginConfiguration
    ) -> Dict[str, forms.Field]:
        parsed_fields = {}
        structure = current_configuration.configuration
        if structure is None:
            raise Exception
        for elem in structure:
            slug = slugify(elem["name"])
            parsed_fields[slug] = self._create_field(elem)
        return parsed_fields

    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data
