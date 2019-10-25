import graphene
import pytest

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.base_plugin import BasePlugin
from saleor.extensions.manager import get_extensions_manager
from saleor.extensions.models import PluginConfiguration
from tests.api.utils import get_graphql_content


class PluginSample(BasePlugin):
    PLUGIN_NAME = "PluginSample"
    CONFIG_STRUCTURE = {
        "Username": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Username input field",
            "label": "Username",
        },
        "Password": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Password input field",
            "label": "Password",
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Use sandbox",
            "label": "Use sandbox",
        },
    }

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
                {
                    "name": "Use sandbox",
                    "value": False,
                    "type": ConfigurationTypeField.BOOLEAN,
                    "help_text": "Use sandbox",
                    "label": "Use sandbox",
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
          plugins(first:1){
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

    plugins = content["data"]["plugins"]["edges"]

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
        if configuration_item["type"] == ConfigurationTypeField.CHOICES:
            assert (
                configuration_item["value"]
                == plugin_configuration.configuration[index]["value"]
            )
        else:
            assert (
                configuration_item["value"]
                == str(plugin_configuration.configuration[index]["value"]).lower()
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
    configuration_id = graphene.Node.to_global_id("Plugin", plugin_configuration.pk)

    query = """
    query plugin($id: ID!){
      plugin(id:$id){
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
    plugin = content["data"]["plugin"]
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


PLUGIN_UPDATE_MUTATION = """
        mutation pluginUpdate(
            $id: ID!, $active: Boolean, $configuration: [ConfigurationItemInput]){
            pluginUpdate(
                id:$id,
                input:{active: $active, configuration: $configuration}
            ){
            plugin{
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

    settings.PLUGINS = ["tests.api.test_extensions.PluginSample"]
    manager = get_extensions_manager()
    plugin = manager.get_plugin_configuration(plugin_name="PluginSample")
    old_configuration = plugin.configuration
    plugin_id = graphene.Node.to_global_id("Plugin", plugin.pk)
    variables = {
        "id": plugin_id,
        "active": active,
        "configuration": [updated_configuration_item],
    }
    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    response = staff_api_client.post_graphql(PLUGIN_UPDATE_MUTATION, variables)
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


def get_config_value(field_name, configuration):
    for elem in configuration:
        if elem["name"] == field_name:
            return elem["value"]


def test_plugin_update_saves_boolean_as_boolean(
    staff_api_client, permission_manage_plugins, settings
):
    settings.PLUGINS = ["tests.api.test_extensions.PluginSample"]
    manager = get_extensions_manager()
    plugin = manager.get_plugin_configuration(plugin_name="PluginSample")
    use_sandbox = get_config_value("Use sandbox", plugin.configuration)
    plugin_id = graphene.Node.to_global_id("Plugin", plugin.pk)
    variables = {
        "id": plugin_id,
        "active": plugin.active,
        "configuration": [{"name": "Use sandbox", "value": True}],
    }
    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    response = staff_api_client.post_graphql(PLUGIN_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    assert len(content["data"]["pluginUpdate"]["errors"]) == 0
    plugin.refresh_from_db()
    use_sandbox_new_value = get_config_value("Use sandbox", plugin.configuration)
    assert type(use_sandbox) == type(use_sandbox_new_value)


class Plugin1(BasePlugin):
    PLUGIN_NAME = "Plugin1"

    @classmethod
    def get_plugin_configuration(cls, queryset) -> "PluginConfiguration":
        qs = queryset.filter(name="Plugin1")
        if qs.exists():
            return qs[0]
        defaults = {
            "name": "Plugin1",
            "description": "Test plugin description_1",
            "active": True,
            "configuration": [],
        }
        return PluginConfiguration.objects.create(**defaults)


class Plugin2Inactive(BasePlugin):
    PLUGIN_NAME = "Plugin2Inactive"

    @classmethod
    def get_plugin_configuration(cls, queryset) -> "PluginConfiguration":
        qs = queryset.filter(name="Plugin2Inactive")
        if qs.exists():
            return qs[0]
        defaults = {
            "name": "Plugin2Inactive",
            "description": "Test plugin description_2",
            "active": False,
            "configuration": [],
        }
        return PluginConfiguration.objects.create(**defaults)


class Active(BasePlugin):
    PLUGIN_NAME = "Plugin1"

    @classmethod
    def get_plugin_configuration(cls, queryset) -> "PluginConfiguration":
        qs = queryset.filter(name="Active")
        if qs.exists():
            return qs[0]
        defaults = {
            "name": "Active",
            "description": "Not working",
            "active": True,
            "configuration": [],
        }
        return PluginConfiguration.objects.create(**defaults)


@pytest.mark.parametrize(
    "plugin_filter, count",
    [
        ({"search": "Plugin1"}, 1),
        ({"search": "description"}, 2),
        ({"active": True}, 2),
        ({"search": "Plugin"}, 2),
        ({"active": "False", "search": "Plugin"}, 1),
    ],
)
def test_plugins_query_with_filter(
    plugin_filter, count, staff_api_client, permission_manage_plugins, settings
):
    settings.PLUGINS = [
        "tests.api.test_extensions.Plugin1",
        "tests.api.test_extensions.Plugin2Inactive",
        "tests.api.test_extensions.Active",
    ]
    query = """
        query ($filter: PluginFilterInput) {
            plugins(first: 5, filter:$filter) {
                totalCount
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    variables = {"filter": plugin_filter}
    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["plugins"]["totalCount"] == count
