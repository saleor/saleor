import graphene
import pytest

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.base_plugin import BasePlugin
from saleor.extensions.manager import get_extensions_manager
from saleor.extensions.models import PluginConfiguration
from tests.api.utils import get_graphql_content


class PluginSample(BasePlugin):
    PLUGIN_NAME = "PluginSample"

    @classmethod
    def get_plugin_configuration(cls, queryset) -> "PluginConfiguration":
        qs = queryset.filter(name="PluginSample")
        if qs.exists():
            return qs[0]
        defaults = {
            "name": "PluginSample",
            "description": "Test plugin description",
            "active": True,
            "configuration": [
                {
                    "name": "Username",
                    "value": "admin",
                    "type": ConfigurationTypeField.STRING,
                    "help_text": "Username input field",
                    "label": "Username",
                },
                {
                    "name": "Password",
                    "value": "123",
                    "type": ConfigurationTypeField.STRING,
                    "help_text": "Password input field",
                    "label": "Password",
                },
            ],
        }
        return PluginConfiguration.objects.create(**defaults)


def test_query_plugin_configurations(
    staff_api_client, permission_manage_plugins, settings
):

    # Enable test plugin
    settings.PLUGINS = ["tests.api.test_extensions.PluginSample"]
    query = """
        {
          pluginConfigurations(first:1){
            edges{
              node{
                name
                description
                active
                id
                configuration{
                  name
                  type
                  value
                  helpText
                  label
                }
              }
            }
          }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)

    plugins = content["data"]["pluginConfigurations"]["edges"]

    assert len(plugins) == 1
    plugin = plugins[0]["node"]
    plugin_configuration = PluginConfiguration.objects.get()

    assert plugin["name"] == plugin_configuration.name
    assert plugin["active"] == plugin_configuration.active
    assert plugin["description"] == plugin_configuration.description

    for index, configuration_item in enumerate(plugin["configuration"]):
        assert (
            configuration_item["name"]
            == plugin_configuration.configuration[index]["name"]
        )
        assert (
            configuration_item["type"]
            == plugin_configuration.configuration[index]["type"].upper()
        )
        assert (
            configuration_item["value"]
            == plugin_configuration.configuration[index]["value"]
        )
        assert (
            configuration_item["helpText"]
            == plugin_configuration.configuration[index]["help_text"]
        )
        assert (
            configuration_item["label"]
            == plugin_configuration.configuration[index]["label"]
        )


def test_query_plugin_configuration(
    staff_api_client, permission_manage_plugins, settings
):
    settings.PLUGINS = ["tests.api.test_extensions.PluginSample"]
    manager = get_extensions_manager()
    plugin_configuration = manager.get_plugin_configuration("PluginSample")
    configuration_id = graphene.Node.to_global_id(
        "PluginConfiguration", plugin_configuration.pk
    )

    query = """
    query pluginConfiguration($id: ID!){
      pluginConfiguration(id:$id){
        name
        description
        active
        configuration{
          name
          value
          type
          helpText
          label
        }
      }
    }
    """
    variables = {"id": configuration_id}
    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    plugin = content["data"]["pluginConfiguration"]
    assert plugin["name"] == plugin_configuration.name
    assert plugin["active"] == plugin_configuration.active
    assert plugin["description"] == plugin_configuration.description

    configuration_item = plugin["configuration"][0]
    assert configuration_item["name"] == plugin_configuration.configuration[0]["name"]
    assert (
        configuration_item["type"]
        == plugin_configuration.configuration[0]["type"].upper()
    )
    assert configuration_item["value"] == plugin_configuration.configuration[0]["value"]
    assert (
        configuration_item["helpText"]
        == plugin_configuration.configuration[0]["help_text"]
    )
    assert configuration_item["label"] == plugin_configuration.configuration[0]["label"]


@pytest.mark.parametrize(
    "active, updated_configuration_item",
    [
        (True, {"name": "Username", "value": "user"}),
        (False, {"name": "Username", "value": "admin@example.com"}),
    ],
)
def test_plugin_configuration_update(
    staff_api_client,
    permission_manage_plugins,
    settings,
    active,
    updated_configuration_item,
):
    query = """
        mutation pluginConfigurationUpdate(
            $id: ID!, $active: Boolean, $configuration: [ConfigurationItemInput]){
            pluginConfigurationUpdate(
                id:$id,
                input:{active: $active, configuration: $configuration}
            ){
            pluginConfiguration{
              name
              active
              configuration{
                name
                value
                type
                helpText
                label
              }
            }
            errors{
              field
              message
            }
          }
        }
    """
    settings.PLUGINS = ["tests.api.test_extensions.PluginSample"]
    manager = get_extensions_manager()
    plugin = manager.get_plugin_configuration(plugin_name="PluginSample")
    old_configuration = plugin.configuration
    plugin_id = graphene.Node.to_global_id("PluginConfiguration", plugin.pk)
    variables = {
        "id": plugin_id,
        "active": active,
        "configuration": [updated_configuration_item],
    }
    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    response = staff_api_client.post_graphql(query, variables)
    get_graphql_content(response)

    plugin.refresh_from_db()
    assert plugin.active == active

    first_configuration_item = plugin.configuration[0]
    assert first_configuration_item["name"] == updated_configuration_item["name"]
    assert first_configuration_item["value"] == updated_configuration_item["value"]
    assert first_configuration_item["type"] == old_configuration[0]["type"]
    assert first_configuration_item["help_text"] == old_configuration[0]["help_text"]
    assert first_configuration_item["label"] == old_configuration[0]["label"]

    second_configuration_item = plugin.configuration[1]
    assert second_configuration_item["name"] == old_configuration[1]["name"]
    assert second_configuration_item["value"] == old_configuration[1]["value"]
    assert second_configuration_item["type"] == old_configuration[1]["type"]
    assert second_configuration_item["help_text"] == old_configuration[1]["help_text"]
    assert second_configuration_item["label"] == old_configuration[1]["label"]
