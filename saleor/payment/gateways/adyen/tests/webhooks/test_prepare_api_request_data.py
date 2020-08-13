from unittest import mock

import pytest

from ...webhooks import prepare_api_request_data


def test_prepare_api_request_data_get():
    # given
    data = {
        "parameters": ["payload", "second_param"],
        "payment_data": "test data",
    }

    request_mock = mock.Mock()
    request_mock.GET = {
        "payload": "payload data",
        "second_param": "second param data",
    }
    request_mock.POST = {}

    # when
    request_data = prepare_api_request_data(request_mock, data)

    # then
    assert request_data == {
        "paymentData": data["payment_data"],
        "details": {"payload": "payload data", "second_param": "second param data"},
    }


def test_prepare_api_request_data_post():
    # given
    data = {
        "parameters": ["payload", "second_param"],
        "payment_data": "test data",
    }

    request_mock = mock.Mock()
    request_mock.GET = {}
    request_mock.POST = {
        "payload": "payload data",
        "second_param": "second param data",
    }

    # when
    request_data = prepare_api_request_data(request_mock, data)

    # then
    assert request_data == {
        "paymentData": data["payment_data"],
        "details": {"payload": "payload data", "second_param": "second param data"},
    }


def test_prepare_api_request_data_lack_of_info_in_data():
    # given
    data = {
        "parameters": ["payload", "second_param"],
    }

    request_mock = mock.Mock()
    request_mock.GET = {}
    request_mock.POST = {
        "payload": "payload data",
        "second_param": "second param data",
    }

    # when
    with pytest.raises(KeyError) as e:
        prepare_api_request_data(request_mock, data)

    # then
    assert (
        e._excinfo[1].args[0]
        == "Cannot perform payment. Lack of payment data and parameters information."
    )


def test_prepare_api_request_data_lack_of_required_parameters_in_request():
    # given
    data = {
        "parameters": ["payload", "second_param"],
        "payment_data": "test data",
    }

    request_mock = mock.Mock()
    request_mock.GET = {}
    request_mock.POST = {
        "payload": "payload data",
    }

    # when
    with pytest.raises(KeyError) as e:
        prepare_api_request_data(request_mock, data)

    # then
    assert (
        e._excinfo[1].args[0]
        == "Cannot perform payment. Lack of required parameters in request."
    )
