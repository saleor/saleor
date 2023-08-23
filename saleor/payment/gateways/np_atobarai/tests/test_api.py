import logging
from decimal import Decimal
from unittest.mock import ANY, Mock, patch

import pytest
import requests
from graphene import Node
from requests_hardened import HTTPSession

from .... import PaymentError
from .. import PaymentStatus, api, const
from ..api_helpers import format_price, get_goods_with_refunds
from ..api_types import NPResponse, PaymentResult
from ..errors import (
    NO_PSP_REFERENCE,
    NO_TRACKING_NUMBER,
    NP_CONNECTION_ERROR,
    SHIPPING_COMPANY_CODE_INVALID,
)
from ..plugin import NPAtobaraiGatewayPlugin


@patch.object(HTTPSession, "request")
def test_refund_payment(
    mocked_request, np_atobarai_plugin, np_payment_data, payment_dummy
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    payment_data.amount = payment_dummy.captured_amount
    psp_reference = "18121200001"
    payment_data.psp_reference = psp_reference
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


def test_refund_payment_no_order(np_atobarai_plugin, np_payment_data, payment_dummy):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    payment_dummy.captured_amount = payment_data.amount + Decimal("3.00")
    payment_dummy.order = None
    payment_dummy.save(update_fields=["order", "captured_amount"])

    # then
    with pytest.raises(PaymentError):
        # when
        plugin.refund_payment(payment_data, None)


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_refund_payment_payment_not_created(
    mocked_request, np_atobarai_plugin, np_payment_data, payment_dummy
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    payment_data.amount = payment_dummy.captured_amount
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


@patch.object(HTTPSession, "request")
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


@patch.object(HTTPSession, "request")
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
@patch.object(HTTPSession, "request")
def test_refund_payment_partial_refund_reregister_transaction(
    mocked_request,
    mocked_change_transaction,
    np_atobarai_plugin,
    np_payment_data,
    payment_dummy,
    fulfillment,
):
    # given
    fulfillment.tracking_number = "123123"
    fulfillment.save(update_fields=["tracking_number"])
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    payment_dummy.captured_amount = payment_data.amount + Decimal("3.00")
    psp_reference = "psp_reference"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["captured_amount", "psp_reference"])
    mocked_change_transaction.return_value = PaymentResult(
        status=PaymentStatus.FOR_REREGISTRATION
    )
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


@patch.object(HTTPSession, "request")
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
    errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not errors
    assert not already_captured


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_report_fulfillment_invalid_shipping_company_code(
    mocked_request, config, fulfillment, payment_dummy
):
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
    fulfillment.store_value_in_private_metadata(
        {const.SHIPPING_COMPANY_CODE_METADATA_KEY: "invalid_shipping_company_code"}
    )

    # when
    errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not already_captured
    assert errors == [f"FR#{SHIPPING_COMPANY_CODE_INVALID}"]


@patch("saleor.payment.gateways.np_atobarai.api_helpers.requests.request")
def test_report_fulfillment_no_psp_reference(
    _mocked_request, config, fulfillment, payment_dummy
):
    # when
    errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not already_captured
    assert errors == [f"FR#{NO_PSP_REFERENCE}"]


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
    errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not already_captured
    assert errors == [f"FR#{NO_TRACKING_NUMBER}"]


@patch.object(HTTPSession, "request")
def test_report_fulfillment_np_errors(
    mocked_request, config, fulfillment, payment_dummy
):
    # given
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    error_codes = ["EPRO0101", "EPRO0102"]
    response = Mock(
        spec=requests.Response,
        status_code=400,
        json=Mock(return_value={"errors": [{"codes": error_codes}]}),
    )
    mocked_request.return_value = response

    # when
    errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not already_captured
    assert errors == [f"FR#{code}" for code in error_codes]


@patch.object(HTTPSession, "request")
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
    errors, already_captured = api.report_fulfillment(
        config, payment_dummy, fulfillment
    )

    # then
    assert not already_captured
    assert errors == [f"FR#{NP_CONNECTION_ERROR}"]
    assert caplog.record_tuples == [
        (ANY, logging.WARNING, "Cannot connect to NP Atobarai.")
    ]


@patch.object(HTTPSession, "request")
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
    _, already_captured = api.report_fulfillment(config, payment_dummy, fulfillment)

    # then
    assert already_captured


@pytest.fixture
def payment_np(payment_dummy):
    payment_dummy.gateway = NPAtobaraiGatewayPlugin.PLUGIN_ID
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
    result = ([], False)
    mocked_report_fulfillment.return_value = result
    order = fulfillment.order
    order.payments.add(payment_np)

    # when
    plugin.tracking_number_updated(fulfillment, None)

    # then
    payment_graphql_id = Node.to_global_id("Payment", payment_np.id)
    mocked_notify_dashboard.assert_called_once_with(
        order, f"Payment with id {payment_graphql_id} was captured"
    )
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
    result = (errors, False)
    mocked_report_fulfillment.return_value = result
    order = fulfillment.order
    order.payments.add(payment_np)

    # when
    plugin.tracking_number_updated(fulfillment, None)

    # then
    payment_graphql_id = Node.to_global_id("Payment", payment_np.id)
    error = ", ".join(errors)
    mocked_notify_dashboard.assert_called_once_with(
        order, f"Error: Cannot capture payment with id {payment_graphql_id} ({error})"
    )
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert caplog.records[0].message == (
        f"Could not capture payment with id {payment_graphql_id} "
        f"in NP Atobarai: {error}"
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
    result = ([], True)
    mocked_report_fulfillment.return_value = result
    order = fulfillment.order
    order.payments.add(payment_np)

    # when
    plugin.tracking_number_updated(fulfillment, None)

    # then
    payment_graphql_id = Node.to_global_id("Payment", payment_np.id)
    mocked_notify_dashboard.assert_called_once_with(
        order,
        f"Error: Payment with id {payment_graphql_id} was already captured",
    )
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert (
        caplog.records[0].message
        == f"Payment with id {payment_graphql_id} was already captured"
    )


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
    mocked_notify_dashboard.assert_called_once_with(
        order, "No active payments for this order"
    )
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert caplog.records[0].message == ("No active payments for this order")


@patch.object(HTTPSession, "request")
def test_change_transaction_success(
    mocked_request, config, payment_dummy, np_payment_data
):
    # given
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(
            return_value={
                "results": [
                    {
                        "authori_result": "00",
                        "np_transaction_id": payment_dummy.psp_reference,
                    }
                ]
            }
        ),
    )
    mocked_request.return_value = response

    # when
    payment_response = api.change_transaction(
        config, payment_dummy, np_payment_data, Mock(), Decimal("12.34")
    )

    # then
    assert payment_response.status == PaymentStatus.SUCCESS


@patch("saleor.payment.gateways.np_atobarai.api.cancel")
@patch.object(HTTPSession, "request")
def test_change_transaction_pending(
    mocked_request, mocked_cancel, config, payment_dummy, np_payment_data
):
    # given
    transaction_id = "123"
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(
            return_value={
                "results": [
                    {
                        "authori_result": "10",
                        "np_transaction_id": transaction_id,
                        "authori_hold": [
                            "RE009",
                            "REE021",
                        ],
                    }
                ]
            }
        ),
    )
    mocked_request.return_value = response

    # when
    payment_response = api.change_transaction(
        config, payment_dummy, np_payment_data, Mock(), Decimal("12.34")
    )

    # then
    mocked_cancel.assert_called_once_with(config, transaction_id)
    assert payment_response.status == PaymentStatus.FAILED


@patch.object(HTTPSession, "request")
def test_change_transaction_post_fulfillment(
    mocked_request, config, payment_dummy, np_payment_data
):
    # given
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(return_value={"errors": [{"codes": ["E0100115"]}]}),
    )
    mocked_request.return_value = response

    # when
    payment_response = api.change_transaction(
        config, payment_dummy, np_payment_data, Mock(), Decimal("12.34")
    )

    # then
    assert payment_response.status == PaymentStatus.FOR_REREGISTRATION


@patch.object(HTTPSession, "request")
def test_change_transaction_failed(
    mocked_request, config, payment_dummy, np_payment_data
):
    # given
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(return_value={"errors": [{"codes": ["E0100050"]}]}),
    )
    mocked_request.return_value = response

    # when
    payment_response = api.change_transaction(
        config, payment_dummy, np_payment_data, Mock(), Decimal("12.34")
    )

    # then
    assert payment_response.status == PaymentStatus.FAILED
    assert payment_response.errors


@patch("saleor.payment.gateways.np_atobarai.api.report")
@patch("saleor.payment.gateways.np_atobarai.api.register")
@patch("saleor.payment.gateways.np_atobarai.api.cancel")
def test_reregister_transaction_success(
    mocked_cancel,
    mocked_register,
    mocked_report,
    config,
    payment_dummy,
    np_payment_data,
):
    # given
    tracking_number = "123"
    shipping_company_code = "50000"
    payment_dummy.psp_reference = "123"
    new_psp_reference = "234"
    mocked_cancel.return_value = NPResponse(result={}, error_codes=[])
    mocked_register.return_value = NPResponse(
        result={
            "np_transaction_id": new_psp_reference,
        },
        error_codes=[],
    )
    mocked_report.return_value = NPResponse(result={}, error_codes=[])

    # when
    goods, billed_amount = get_goods_with_refunds(
        config, payment_dummy, np_payment_data
    )
    payment_response = api.reregister_transaction_for_partial_return(
        config,
        payment_dummy,
        np_payment_data,
        shipping_company_code,
        tracking_number,
        goods,
        billed_amount,
    )

    # then
    mocked_cancel.assert_called_once_with(config, payment_dummy.psp_reference)
    mocked_register.assert_called_once_with(
        config,
        np_payment_data,
        int(format_price(billed_amount, np_payment_data.currency)),
        goods,
    )
    mocked_report.assert_called_once_with(
        config, shipping_company_code, new_psp_reference, tracking_number
    )
    assert payment_response.status == PaymentStatus.SUCCESS
    assert payment_response.psp_reference == new_psp_reference


def test_reregister_transaction_no_psp_reference(payment_dummy, np_payment_data):
    # when
    payment_response = api.reregister_transaction_for_partial_return(
        Mock(),
        payment_dummy,
        np_payment_data,
        Mock(),
        Mock(),
        Mock(),
        Decimal("12.34"),
    )

    # then
    assert payment_response.status == PaymentStatus.FAILED
    assert payment_response.errors == [f"TR#{NO_PSP_REFERENCE}"]


@patch("saleor.payment.gateways.np_atobarai.api.cancel")
def test_reregister_transaction_cancel_error(
    mocked_cancel, config, payment_dummy, np_payment_data
):
    # given
    payment_dummy.psp_reference = "123"
    error_codes = ["1", "2", "3"]
    mocked_cancel.return_value = NPResponse(result={}, error_codes=error_codes)

    # when
    payment_response = api.reregister_transaction_for_partial_return(
        config, payment_dummy, np_payment_data, Mock(), Mock(), Mock(), Decimal("12.34")
    )

    # then
    assert payment_response.status == PaymentStatus.FAILED
    assert payment_response.errors == [f"TC#{code}" for code in error_codes]


@patch("saleor.payment.gateways.np_atobarai.api.report")
@patch("saleor.payment.gateways.np_atobarai.api.register")
@patch("saleor.payment.gateways.np_atobarai.api.cancel")
def test_reregister_transaction_report_error(
    mocked_cancel,
    mocked_register,
    mocked_report,
    config,
    payment_dummy,
    np_payment_data,
):
    # given
    tracking_number = "123"
    shipping_company_code = "50000"
    payment_dummy.psp_reference = "123"
    new_psp_reference = "234"
    error_codes = ["1", "2", "3"]
    mocked_cancel.return_value = NPResponse(result={}, error_codes=[])
    mocked_register.return_value = NPResponse(
        result={
            "np_transaction_id": new_psp_reference,
        },
        error_codes=[],
    )
    mocked_report.return_value = NPResponse(result={}, error_codes=error_codes)

    # when
    payment_response = api.reregister_transaction_for_partial_return(
        config,
        payment_dummy,
        np_payment_data,
        shipping_company_code,
        tracking_number,
        Mock(),
        Decimal("12.34"),
    )

    # then
    assert payment_response.status == PaymentStatus.FAILED
    assert payment_response.errors == [f"FR#{code}" for code in error_codes]


@patch("saleor.payment.gateways.np_atobarai.api.register")
@patch("saleor.payment.gateways.np_atobarai.api.cancel")
def test_reregister_transaction_general_error(
    mocked_cancel,
    mocked_register,
    config,
    payment_dummy,
    np_payment_data,
):
    # given
    payment_dummy.psp_reference = "123"
    mocked_cancel.return_value = NPResponse(result={}, error_codes=[])
    error_codes = ["1", "2", "3"]
    mocked_register.return_value = NPResponse(result={}, error_codes=error_codes)

    # when
    payment_response = api.reregister_transaction_for_partial_return(
        config, payment_dummy, np_payment_data, Mock(), Mock(), Mock(), Decimal("12.34")
    )

    # then
    assert payment_response.status == PaymentStatus.FAILED
    assert payment_response.errors == [f"TR#{code}" for code in error_codes]


@patch("saleor.payment.gateways.np_atobarai.api.cancel")
@patch("saleor.payment.gateways.np_atobarai.api.register")
def test_register_transaction_pending(
    mocked_register, mocked_cancel, config, np_payment_data
):
    # given
    transaction_id = "123123123"
    errors = ["RE009", "RE015"]
    register_result = {
        "authori_result": "10",
        "np_transaction_id": transaction_id,
        "authori_hold": errors,
    }
    mocked_register.return_value = NPResponse(result=register_result, error_codes=[])
    mocked_cancel.return_value = NPResponse(result={}, error_codes=[])

    # when
    payment_response = api.register_transaction(config, np_payment_data)

    # then
    mocked_register.assert_called_once()
    mocked_cancel.assert_called_once_with(config, transaction_id)
    assert payment_response.status == PaymentStatus.PENDING
    assert payment_response.errors == [f"TR#{e}" for e in errors]


@patch("saleor.payment.gateways.np_atobarai.api.cancel")
@patch("saleor.payment.gateways.np_atobarai.api.register")
def test_register_transaction_pending_unrecoverable(
    mocked_register, mocked_cancel, config, np_payment_data, caplog
):
    # given
    transaction_id = "123123123"
    errors = ["RE009", "RE015"]
    register_result = {
        "authori_result": "10",
        "np_transaction_id": transaction_id,
        "authori_hold": errors,
    }
    mocked_register.return_value = NPResponse(result=register_result, error_codes=[])
    cancel_errors = ["1", "2", "3"]
    mocked_cancel.return_value = NPResponse(result={}, error_codes=cancel_errors)

    # when
    payment_response = api.register_transaction(config, np_payment_data)

    # then
    mocked_register.assert_called_once()
    mocked_cancel.assert_called_once_with(config, transaction_id)
    assert payment_response.status == PaymentStatus.PENDING
    assert payment_response.errors == [f"TR#{e}" for e in errors]
    assert caplog.record_tuples == [(ANY, logging.ERROR, ANY)]


def test_cancel_transaction_no_payment(np_payment_data):
    # given
    np_payment_data.psp_reference = ""

    # when
    payment_response = api.cancel_transaction(Mock(), np_payment_data)

    # then
    assert payment_response.errors == [f"TC#{NO_PSP_REFERENCE}"]
