from unittest import mock
from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError

from saleor.plugins.models import PluginConfiguration


@mock.patch("saleor.payment.gateways.np_atobarai.api.requests.request")
@pytest.mark.parametrize("status_code", [200, 400])
def test_validate_plugin_configuration_valid_credentials(
    mocked_request, np_atobarai_plugin, status_code
):
    # given
    plugin = np_atobarai_plugin()
    response = Mock()
    response.status_code = status_code
    mocked_request.return_value = response
    configuration = PluginConfiguration.objects.get()
    # when
    plugin.validate_plugin_configuration(configuration)
    # then: no exception


@mock.patch("saleor.payment.gateways.np_atobarai.api.requests.request")
@pytest.mark.parametrize("status_code", [401, 403])
def test_validate_plugin_configuration_invalid_credentials(
    mocked_request, np_atobarai_plugin, status_code
):
    # given
    plugin = np_atobarai_plugin()
    response = Mock()
    response.status_code = status_code
    mocked_request.return_value = response
    configuration = PluginConfiguration.objects.get()
    # then
    with pytest.raises(ValidationError):
        # when
        plugin.validate_plugin_configuration(configuration)


@mock.patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_validate_plugin_configuration_missing_data(mocked_request, np_atobarai_plugin):
    # given
    plugin = np_atobarai_plugin()
    response = Mock()
    response.status_code = 200
    mocked_request.return_value = response
    plugin_configuration = PluginConfiguration.objects.get()
    for d in plugin_configuration.configuration:
        d["value"] = None
    plugin_configuration.save()

    # when
    with pytest.raises(ValidationError) as excinfo:
        plugin.validate_plugin_configuration(plugin_configuration)

    # then
    assert len(excinfo.value.error_dict) == 3
