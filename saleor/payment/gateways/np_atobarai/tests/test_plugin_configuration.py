from unittest import mock
from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError

from .....plugins.models import PluginConfiguration
from .... import PaymentError


@pytest.fixture
def np_void_payment_data(dummy_payment_data):
    return dummy_payment_data


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
    plugin = np_atobarai_plugin(merchant_code=None, sp_code=None, terminal_id=None)
    response = Mock()
    response.status_code = 200
    mocked_request.return_value = response
    plugin_configuration = PluginConfiguration.objects.get()

    # when
    with pytest.raises(ValidationError) as excinfo:
        plugin.validate_plugin_configuration(plugin_configuration)

    # then
    assert len(excinfo.value.error_dict) == 3


@mock.patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_void_payment(
    mocked_request, np_atobarai_plugin, np_void_payment_data, payment_dummy
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_void_payment_data
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    response = Mock()
    response.json = Mock(
        return_value={"results": [{"np_transaction_id": psp_reference}]}
    )
    mocked_request.return_value = response

    # when
    gateway_response = plugin.void_payment(payment_data, None)

    # then
    assert gateway_response.is_success
    assert gateway_response.psp_reference == psp_reference


@mock.patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_void_payment_payment_not_created(
    mocked_request, np_atobarai_plugin, np_void_payment_data, payment_dummy
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_void_payment_data
    response = Mock()
    response.json = Mock(
        return_value={"results": [{"np_transaction_id": "18121200001"}]}
    )
    mocked_request.return_value = response

    # then
    with pytest.raises(PaymentError):
        # when
        plugin.void_payment(payment_data, None)


@mock.patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_void_payment_np_errors(
    mocked_request, np_atobarai_plugin, np_void_payment_data, payment_dummy
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_void_payment_data
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    response = Mock()
    response.json = Mock(return_value={"errors": [{"codes": ["E0100002", "E0100003"]}]})
    mocked_request.return_value = response

    # when
    gateway_response = plugin.void_payment(payment_data, None)

    # then
    assert not gateway_response.is_success
    assert gateway_response.error
