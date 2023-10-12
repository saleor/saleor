from unittest import mock
from unittest.mock import Mock

import pytest
import requests
from django.core.exceptions import ValidationError
from requests_hardened import HTTPSession

from ..plugin import NPAtobaraiGatewayPlugin


@mock.patch.object(HTTPSession, "request")
@pytest.mark.parametrize("status_code", [200, 400])
def test_validate_plugin_configuration_valid_credentials(
    mocked_request, np_atobarai_plugin, status_code
):
    # given
    plugin = np_atobarai_plugin()
    response = Mock(spec=requests.Response, status_code=status_code)
    mocked_request.return_value = response
    # when
    NPAtobaraiGatewayPlugin.validate_plugin_configuration(plugin)
    # then: no exception


@mock.patch.object(HTTPSession, "request")
@pytest.mark.parametrize("status_code", [401, 403])
def test_validate_plugin_configuration_invalid_credentials(
    mocked_request, np_atobarai_plugin, status_code
):
    # given
    plugin = np_atobarai_plugin()
    response = Mock(spec=requests.Response, status_code=status_code, request=Mock())
    mocked_request.return_value = response
    # then
    with pytest.raises(ValidationError):
        # when
        NPAtobaraiGatewayPlugin.validate_plugin_configuration(plugin)


@mock.patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_validate_plugin_configuration_missing_data(mocked_request, np_atobarai_plugin):
    # given
    plugin = np_atobarai_plugin(merchant_code=None, sp_code=None, terminal_id=None)
    response = Mock(spec=requests.Response, status_code=200)
    mocked_request.return_value = response

    # when
    with pytest.raises(ValidationError) as excinfo:
        NPAtobaraiGatewayPlugin.validate_plugin_configuration(plugin)

    # then
    assert len(excinfo.value.error_dict) == 3


@mock.patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_validate_plugin_configuration_invalid_shipping_company_code(
    mocked_request, np_atobarai_plugin
):
    # given
    plugin = np_atobarai_plugin(shipping_company="00")
    response = Mock(spec=requests.Response, status_code=200)
    mocked_request.return_value = response

    # when
    with pytest.raises(ValidationError) as excinfo:
        NPAtobaraiGatewayPlugin.validate_plugin_configuration(plugin)

    # then
    assert "shipping_company" in excinfo.value.error_dict


@mock.patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_validate_plugin_configuration_inactive(mocked_request, np_atobarai_plugin):
    # given
    plugin = np_atobarai_plugin(active=False)

    # when
    NPAtobaraiGatewayPlugin.validate_plugin_configuration(plugin)

    # then
    mocked_request.assert_not_called()
