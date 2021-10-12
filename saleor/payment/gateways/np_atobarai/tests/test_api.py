from unittest.mock import Mock, patch

import pytest
import requests

from saleor.payment.gateways.np_atobarai import api, get_api_config


@pytest.fixture
def config(np_atobarai_plugin):
    return get_api_config(np_atobarai_plugin().config.connection_params)


@patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_report_fulfillment(mocked_request, config, fulfillment, payment_dummy):
    # given
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    fulfillment.order.payments.add(payment_dummy)
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(return_value={"results": [{"np_transaction_id": psp_reference}]}),
    )
    mocked_request.return_value = response

    # when
    errors = api.report_fulfillment(config, fulfillment)

    # then
    assert not errors


@patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_report_fulfillment_no_payment(_mocked_request, config, fulfillment):
    # when
    errors = api.report_fulfillment(config, fulfillment)

    # then
    assert errors == ["Payment does not exist for this order."]


@patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_report_fulfillment_no_psp_reference(
    _mocked_request, config, fulfillment, payment_dummy
):
    # given
    fulfillment.order.payments.add(payment_dummy)

    # when
    errors = api.report_fulfillment(config, fulfillment)

    # then
    assert errors == ["Payment does not have psp reference."]


@patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_report_fulfillment_no_tracking_number(
    _mocked_request, config, fulfillment, payment_dummy
):
    # given
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    fulfillment.order.payments.add(payment_dummy)
    fulfillment.tracking_number = ""

    # when
    errors = api.report_fulfillment(config, fulfillment)

    # then
    assert errors == ["Fulfillment does not have tracking number."]


@patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_report_fulfillment_np_errors(
    mocked_request, config, fulfillment, payment_dummy
):
    # given
    psp_reference = "18121200001"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])
    fulfillment.order.payments.add(payment_dummy)
    response = Mock(
        spec=requests.Response,
        status_code=400,
        json=Mock(return_value={"errors": [{"codes": ["EPRO0101", "EPRO0102"]}]}),
    )
    mocked_request.return_value = response

    # when
    errors = api.report_fulfillment(config, fulfillment)

    # then
    assert set(errors) == {
        "Please confirm that 1, 000 or fewer sets of normal transactions are set.",
        "Please confirm that at least one normal transaction is set.",
    }
