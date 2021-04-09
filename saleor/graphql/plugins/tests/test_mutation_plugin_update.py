import copy

import pytest

from ....plugins.error_codes import PluginErrorCode
from ....plugins.manager import get_plugins_manager
from ....plugins.models import PluginConfiguration
from ....plugins.tests.sample_plugins import PluginSample
from ....plugins.tests.utils import get_config_value
from ...tests.utils import assert_no_permission, get_graphql_content

PLUGIN_UPDATE_MUTATION = """
    mutation pluginUpdate(
        $id: ID!
        $active: Boolean
        $configuration: [ConfigurationItemInput]
    ) {
        pluginUpdate(
            id: $id
            input: { active: $active, configuration: $configuration }
        ) {
            plugin {
                name
                description
                globalConfiguration{
                  active
                  configuration{
                    name
                    value
                    helpText
                    type
                    label
                  }
                  channel{
                    id
                    slug
                  }
                }
                channelConfigurations{
                  active
                  channel{
                    id
                    slug
                  }
                  configuration{
                    name
                    value
                    helpText
                    type
                    label
                  }
                }
            }
            errors {
                field
                message
            }
            pluginsErrors {
                field
                code
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

    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    manager = get_plugins_manager()
    plugin = manager.get_plugin(PluginSample.PLUGIN_ID)
    old_configuration = copy.deepcopy(plugin.configuration)

    variables = {
        "id": plugin.PLUGIN_ID,
        "active": active,
        "configuration": [updated_configuration_item],
    }
    response = staff_api_client_can_manage_plugins.post_graphql(
        PLUGIN_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)

    plugin_data = content["data"]["pluginUpdate"]["plugin"]

    assert plugin_data["name"] == plugin.PLUGIN_NAME
    assert plugin_data["description"] == plugin.PLUGIN_DESCRIPTION

    plugin = PluginConfiguration.objects.get(identifier=PluginSample.PLUGIN_ID)
    assert plugin.active == active

    first_configuration_item = plugin.configuration[0]
    assert first_configuration_item["name"] == updated_configuration_item["name"]
    assert first_configuration_item["value"] == updated_configuration_item["value"]

    second_configuration_item = plugin.configuration[1]
    assert second_configuration_item["name"] == old_configuration[1]["name"]
    assert second_configuration_item["value"] == old_configuration[1]["value"]

    configuration = plugin_data["globalConfiguration"]["configuration"]
    assert configuration is not None
    assert configuration[0]["name"] == updated_configuration_item["name"]
    assert configuration[0]["value"] == updated_configuration_item["value"]


def test_plugin_configuration_update_containing_invalid_plugin_id(
    staff_api_client_can_manage_plugins,
):
    variables = {
        "id": "fake-id",
        "active": True,
        "configuration": [{"name": "Username", "value": "user"}],
    }
    response = staff_api_client_can_manage_plugins.post_graphql(
        PLUGIN_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    assert content["data"]["pluginUpdate"]["pluginsErrors"][0] == {
        "field": "id",
        "code": PluginErrorCode.NOT_FOUND.name,
    }


def test_plugin_update_saves_boolean_as_boolean(
    staff_api_client_can_manage_plugins, settings
):
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    manager = get_plugins_manager()
    plugin = manager.get_plugin(PluginSample.PLUGIN_ID)
    use_sandbox = get_config_value("Use sandbox", plugin.configuration)
    variables = {
        "id": plugin.PLUGIN_ID,
        "active": plugin.active,
        "configuration": [{"name": "Use sandbox", "value": True}],
    }
    response = staff_api_client_can_manage_plugins.post_graphql(
        PLUGIN_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    assert len(content["data"]["pluginUpdate"]["errors"]) == 0
    use_sandbox_new_value = get_config_value("Use sandbox", plugin.configuration)
    assert type(use_sandbox) == type(use_sandbox_new_value)

    def test_plugin_configuration_update_as_customer_user(user_api_client, settings):
        settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.PluginSample"]
        manager = get_plugins_manager()
        plugin = manager.get_plugin(PluginSample.PLUGIN_ID)

        variables = {
            "id": plugin.PLUGIN_ID,
            "active": True,
            "configuration": [{"name": "Username", "value": "user"}],
        }
        response = user_api_client.post_graphql(PLUGIN_UPDATE_MUTATION, variables)

        assert_no_permission(response)
