import logging
from decimal import Decimal
from unittest.mock import ANY, Mock, patch

import pytest
import requests

from .... import PaymentError
from .. import api, get_api_config


@pytest.fixture
def config(np_atobarai_plugin):
    return get_api_config(np_atobarai_plugin().config.connection_params)


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_refund_payment(
    mocked_request, np_atobarai_plugin, np_payment_data, payment_dummy
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(return_value={"results": [{"np_transaction_id": psp_reference}]}),
    )
    mocked_request.return_value = response

    # when
    gateway_response = plugin.refund_payment(payment_data, None)

    # then
    assert gateway_response.is_success


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_refund_payment_payment_not_created(
    mocked_request, np_atobarai_plugin, np_payment_data, payment_dummy
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(return_value={"results": [{"np_transaction_id": "18121200001"}]}),
    )
    mocked_request.return_value = response

    # when
    gateway_response = plugin.refund_payment(payment_data, None)

    # then
    assert not gateway_response.is_success


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_refund_payment_np_errors(
    mocked_request, np_atobarai_plugin, np_payment_data, payment_dummy
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    response = Mock(
        spec=requests.Response,
        status_code=400,
        json=Mock(return_value={"errors": [{"codes": ["E0100002", "E0100003"]}]}),
    )
    mocked_request.return_value = response

    # when
    gateway_response = plugin.refund_payment(payment_data, None)

    # then
    assert not gateway_response.is_success
    assert gateway_response.error


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_refund_payment_no_payment(
    _mocked_request, np_atobarai_plugin, np_payment_data, payment_dummy
):
    # given
    payment_id = -1
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    payment_data.payment_id = payment_id

    # when
    with pytest.raises(PaymentError) as excinfo:
        plugin.refund_payment(payment_data, None)

    # then
    assert excinfo.value.message == f"Payment with id {payment_id} does not exist."


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_refund_payment_partial_refund_change_transaction(
    mocked_request, np_atobarai_plugin, np_payment_data, payment_dummy
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    payment_dummy.captured_amount = payment_data.amount + Decimal("3.00")
    psp_reference = "psp_reference"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["captured_amount", "psp_reference"])
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(
            return_value={
                "results": [
                    {
                        "np_transaction_id": psp_reference,
                        "authori_result": "00",
                    }
                ]
            }
        ),
    )
    mocked_request.return_value = response

    # when
    gateway_response = plugin.refund_payment(payment_data, None)

    # then
    assert gateway_response.is_success


@patch("saleor.payment.gateways.np_atobarai.api.change_transaction")
@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_refund_payment_partial_refund_reregister_transaction(
    mocked_request,
    mocked_change_transaction,
    np_atobarai_plugin,
    np_payment_data,
    payment_dummy,
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    payment_dummy.captured_amount = payment_data.amount + Decimal("3.00")
    psp_reference = "psp_reference"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["captured_amount", "psp_reference"])
    mocked_change_transaction.return_value = None
    new_psp_reference = "new_psp_reference"
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(
            return_value={
                "results": [
                    {
                        "base_np_transaction_id": payment_dummy.psp_reference,
                        "np_transaction_id": new_psp_reference,
                    }
                ]
            }
        ),
    )
    mocked_request.return_value = response

    # when
    gateway_response = plugin.refund_payment(payment_data, None)

    # then
    assert gateway_response.is_success
    assert gateway_response.psp_reference == new_psp_reference


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_report_fulfillment(mocked_request, config, fulfillment, payment_dummy):
    # given
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(return_value={"results": [{"np_transaction_id": psp_reference}]}),
    )
    mocked_request.return_value = response

    # when
    _, errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not errors
    assert not already_captured


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_report_fulfillment_no_psp_reference(
    _mocked_request, config, fulfillment, payment_dummy
):
    # when
    _, errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not already_captured
    assert errors == ["Payment does not have psp reference."]


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_report_fulfillment_no_tracking_number(
    _mocked_request, config, fulfillment, payment_dummy
):
    # given
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    fulfillment.tracking_number = ""

    # when
    _, errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not already_captured
    assert errors == ["Fulfillment does not have tracking number."]


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_report_fulfillment_np_errors(
    mocked_request, config, fulfillment, payment_dummy
):
    # given
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    response = Mock(
        spec=requests.Response,
        status_code=400,
        json=Mock(return_value={"errors": [{"codes": ["EPRO0101", "EPRO0102"]}]}),
    )
    mocked_request.return_value = response

    # when
    _, errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not already_captured
    assert set(errors) == {
        "Please confirm that 1000 or fewer sets of normal transactions are set.",
        "Please confirm that at least one normal transaction is set.",
    }


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_report_fulfillment_connection_errors(
    mocked_request, config, fulfillment, payment_dummy, caplog
):
    # given
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    response = Mock(
        spec=requests.Response,
        status_code=404,
    )
    mocked_request.return_value = response

    # when
    _, errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not already_captured
    error_message = "Cannot connect to NP Atobarai."
    assert errors == [error_message]
    assert caplog.record_tuples == [(ANY, logging.WARNING, error_message)]


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_report_fulfillment_already_captured(
    mocked_request, config, fulfillment, payment_dummy
):
    # given
    payment_dummy.psp_reference = "123123123"
    response = Mock(
        spec=requests.Response,
        status_code=400,
        json=Mock(return_value={"errors": [{"codes": ["E0100115"]}]}),
    )
    mocked_request.return_value = response

    # when
    _, _, already_captured = api.report_fulfillment(config, payment_dummy, fulfillment)

    # then
    assert already_captured


@pytest.fixture
def payment_np(payment_dummy):
    payment_dummy.gateway = "mirumee.payments.np-atobarai"
    payment_dummy.save(update_fields=["gateway"])
    return payment_dummy


@patch("saleor.payment.gateways.np_atobarai.notify_dashboard")
@patch("saleor.payment.gateways.np_atobarai.api.report_fulfillment")
def test_tracking_number_updated(
    mocked_report_fulfillment,
    mocked_notify_dashboard,
    np_atobarai_plugin,
    payment_np,
    fulfillment,
    caplog,
):
    # given
    plugin = np_atobarai_plugin()
    result = ("", [], False)
    mocked_report_fulfillment.return_value = result
    order = fulfillment.order
    order.payments.add(payment_np)

    # when
    plugin.tracking_number_updated(fulfillment, None)

    # then
    mocked_notify_dashboard.assert_called_once_with(order, "Captured payment")
    assert not caplog.record_tuples


@patch("saleor.payment.gateways.np_atobarai.notify_dashboard")
@patch("saleor.payment.gateways.np_atobarai.api.report_fulfillment")
def test_tracking_number_updated_errors(
    mocked_report_fulfillment,
    mocked_notify_dashboard,
    np_atobarai_plugin,
    payment_np,
    fulfillment,
    caplog,
):
    # given
    errors = ["error1", "error2"]
    plugin = np_atobarai_plugin()
    result = ("", errors, False)
    mocked_report_fulfillment.return_value = result
    order = fulfillment.order
    order.payments.add(payment_np)

    # when
    plugin.tracking_number_updated(fulfillment, None)

    # then
    mocked_notify_dashboard.assert_called_once_with(order, "Capture Error for payment")
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert caplog.records[0].message == (
        f"Could not capture payment in NP Atobarai: {', '.join(errors)}"
    )


@patch("saleor.payment.gateways.np_atobarai.notify_dashboard")
@patch("saleor.payment.gateways.np_atobarai.api.report_fulfillment")
def test_tracking_number_updated_already_captured(
    mocked_report_fulfillment,
    mocked_notify_dashboard,
    np_atobarai_plugin,
    payment_np,
    fulfillment,
    caplog,
):
    # given
    plugin = np_atobarai_plugin()
    result = ("", [], True)
    mocked_report_fulfillment.return_value = result
    order = fulfillment.order
    order.payments.add(payment_np)

    # when
    plugin.tracking_number_updated(fulfillment, None)

    # then
    mocked_notify_dashboard.assert_called_once_with(
        order, "Error: Payment was already captured"
    )
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert caplog.records[0].message == "Payment was already captured"


@patch("saleor.payment.gateways.np_atobarai.notify_dashboard")
@patch("saleor.payment.gateways.np_atobarai.api.report_fulfillment")
def test_tracking_number_updated_no_payments(
    _mocked_report_fulfillment,
    mocked_notify_dashboard,
    np_atobarai_plugin,
    fulfillment,
    caplog,
):
    # given
    plugin = np_atobarai_plugin()
    order = fulfillment.order

    # when
    plugin.tracking_number_updated(fulfillment, None)

    # then
    mocked_notify_dashboard.assert_called_once_with(order, "Capture Error for payment")
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert caplog.records[0].message == (
        "Could not capture payment in NP Atobarai: No active payments for this order"
    )
