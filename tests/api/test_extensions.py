import graphene
import pytest

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.manager import get_extensions_manager
from saleor.extensions.models import PluginConfiguration
from tests.api.utils import get_graphql_content
from tests.extensions.helpers import get_config_value
from tests.extensions.sample_plugins import PluginSample


@pytest.fixture
def staff_api_client_can_manage_plugins(staff_api_client, permission_manage_plugins):
    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    return staff_api_client


def test_query_plugin_configurations(staff_api_client_can_manage_plugins, settings):

    # Enable test plugin
    settings.PLUGINS = ["tests.extensions.sample_plugins.PluginSample"]
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
    response = staff_api_client_can_manage_plugins.post_graphql(query)
    content = get_graphql_content(response)

    plugins = content["data"]["plugins"]["edges"]

    assert len(plugins) == 1
    plugin = plugins[0]["node"]
    plugin_configuration = PluginConfiguration.objects.get()
    confiugration_structure = PluginSample.CONFIG_STRUCTURE

    assert plugin["name"] == plugin_configuration.name
    assert plugin["active"] == plugin_configuration.active
    assert plugin["description"] == plugin_configuration.description

    for index, configuration_item in enumerate(plugin["configuration"]):
        assert (
            configuration_item["name"]
            == plugin_configuration.configuration[index]["name"]
        )

        if (
            confiugration_structure[configuration_item["name"]]["type"]
            == ConfigurationTypeField.STRING
        ):
            assert (
                configuration_item["value"]
                == plugin_configuration.configuration[index]["value"]
            )
        else:
            assert (
                configuration_item["value"]
                == str(plugin_configuration.configuration[index]["value"]).lower()
            )


def test_query_plugin_configuration(staff_api_client_can_manage_plugins, settings):
    settings.PLUGINS = ["tests.extensions.sample_plugins.PluginSample"]
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
    response = staff_api_client_can_manage_plugins.post_graphql(query, variables)
    content = get_graphql_content(response)
    plugin = content["data"]["plugin"]
    assert plugin["name"] == plugin_configuration.name
    assert plugin["active"] == plugin_configuration.active
    assert plugin["description"] == plugin_configuration.description

    configuration_item = plugin["configuration"][0]
    assert configuration_item["name"] == plugin_configuration.configuration[0]["name"]
    assert configuration_item["value"] == plugin_configuration.configuration[0]["value"]


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
    staff_api_client_can_manage_plugins, settings, active, updated_configuration_item
):

    settings.PLUGINS = ["tests.extensions.sample_plugins.PluginSample"]
    manager = get_extensions_manager()
    plugin = manager.get_plugin_configuration(plugin_name="PluginSample")
    old_configuration = plugin.configuration
    plugin_id = graphene.Node.to_global_id("Plugin", plugin.pk)
    variables = {
        "id": plugin_id,
        "active": active,
        "configuration": [updated_configuration_item],
    }
    response = staff_api_client_can_manage_plugins.post_graphql(
        PLUGIN_UPDATE_MUTATION, variables
    )
    get_graphql_content(response)

    plugin.refresh_from_db()
    assert plugin.active == active

    first_configuration_item = plugin.configuration[0]
    assert first_configuration_item["name"] == updated_configuration_item["name"]
    assert first_configuration_item["value"] == updated_configuration_item["value"]

    second_configuration_item = plugin.configuration[1]
    assert second_configuration_item["name"] == old_configuration[1]["name"]
    assert second_configuration_item["value"] == old_configuration[1]["value"]


def test_plugin_update_saves_boolean_as_boolean(
    staff_api_client_can_manage_plugins, settings
):
    settings.PLUGINS = ["tests.extensions.sample_plugins.PluginSample"]
    manager = get_extensions_manager()
    plugin = manager.get_plugin_configuration(plugin_name="PluginSample")
    use_sandbox = get_config_value("Use sandbox", plugin.configuration)
    plugin_id = graphene.Node.to_global_id("Plugin", plugin.pk)
    variables = {
        "id": plugin_id,
        "active": plugin.active,
        "configuration": [{"name": "Use sandbox", "value": True}],
    }
    response = staff_api_client_can_manage_plugins.post_graphql(
        PLUGIN_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    assert len(content["data"]["pluginUpdate"]["errors"]) == 0
    plugin.refresh_from_db()
    use_sandbox_new_value = get_config_value("Use sandbox", plugin.configuration)
    assert type(use_sandbox) == type(use_sandbox_new_value)


@pytest.mark.parametrize(
    "plugin_filter, count",
    [
        ({"search": "PluginSample"}, 1),
        ({"search": "description"}, 2),
        ({"active": True}, 2),
        ({"search": "Plugin"}, 2),
        ({"active": "False", "search": "Plugin"}, 1),
    ],
)
def test_plugins_query_with_filter(
    plugin_filter, count, staff_api_client_can_manage_plugins, settings
):
    settings.PLUGINS = [
        "tests.extensions.sample_plugins.PluginSample",
        "tests.extensions.sample_plugins.Plugin2Inactive",
        "tests.extensions.sample_plugins.Active",
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
    response = staff_api_client_can_manage_plugins.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["plugins"]["totalCount"] == count
