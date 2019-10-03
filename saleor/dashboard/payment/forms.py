from typing import Any, Dict

from django import forms
from django.utils.text import slugify

from ...extensions import ConfigurationTypeField
from ...extensions.models import PluginConfiguration

TYPE_TO_FIELD = {
    ConfigurationTypeField.STRING: forms.CharField,
    ConfigurationTypeField.BOOLEAN: forms.BooleanField,
}


class GatewayConfigurationForm(forms.Form):
    active = forms.BooleanField(required=False)

    def __init__(self, plugin, *args, **kwargs):
        self.plugin = plugin
        super().__init__(*args, **kwargs)
        current_configuration = self._get_current_configuration()
        # add new fields specified for gateway
        self.fields.update(self._prepare_fields_for_given_config(current_configuration))
        self.fields["active"].initial = current_configuration.active

    def _get_current_configuration(self) -> PluginConfiguration:
        qs = PluginConfiguration.objects.all()
        return self.plugin.get_plugin_configuration(qs)

    def _create_field(self, structure: Dict[str, Any]) -> forms.Field:
        label = structure["label"]
        help_text = structure["help_text"]
        elem_type = structure["type"]
        current_value = structure["value"]
        return TYPE_TO_FIELD[elem_type](
            label=label, help_text=help_text, initial=current_value
        )

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
