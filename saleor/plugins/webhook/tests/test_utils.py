import copy

import pytest

from ....payment.interface import PaymentGateway
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.transport.list_stored_payment_methods import (
    get_credit_card_info,
    get_list_stored_payment_methods_from_response,
    get_payment_method_from_response,
)
from ....webhook.transport.utils import (
    generate_cache_key_for_webhook,
    to_payment_app_id,
)


@pytest.fixture
def payment_method_response():
    return {
        "id": "method-1",
        "supportedPaymentFlows": ["INTERACTIVE"],
        "type": "Credit Card",
        "creditCardInfo": {
            "brand": "visa",
            "lastDigits": "1234",
            "expMonth": 1,
            "expYear": 2023,
            "firstDigits": "123456",
        },
        "name": "***1234",
        "data": {"some": "data"},
    }


def test_different_target_urls_produce_different_cache_key(checkout_with_item):
    # given
    target_url_1 = "http://example.com/1"
    target_url_2 = "http://example.com/2"

    payload = {"field": "1", "field2": "2"}

    # when
    cache_key_1 = generate_cache_key_for_webhook(
        payload,
        target_url_1,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        1,
    )
    cache_key_2 = generate_cache_key_for_webhook(
        payload,
        target_url_2,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        1,
    )

    # then
    assert cache_key_1 != cache_key_2


def test_different_payload_produce_different_cache_key(checkout_with_item):
    # given
    target_url = "http://example.com/1"

    payload_1 = {"field": "1", "field2": "2"}
    payload_2 = {"field": "1", "field2": "3"}

    # when
    cache_key_1 = generate_cache_key_for_webhook(
        payload_1,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        1,
    )
    cache_key_2 = generate_cache_key_for_webhook(
        payload_2,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        1,
    )

    # then
    assert cache_key_1 != cache_key_2


def test_different_event_produce_different_cache_key(checkout_with_item):
    # given
    target_url = "http://example.com/1"

    payload = {"field": "1", "field2": "2"}

    # when
    cache_key_1 = generate_cache_key_for_webhook(
        payload, target_url, WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, 1
    )
    cache_key_2 = generate_cache_key_for_webhook(
        payload, target_url, WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS, 1
    )

    # then
    assert cache_key_1 != cache_key_2


def test_different_app_produce_different_cache_key():
    # given
    target_url = "http://example.com/1"
    first_app_id = 1
    second_app_id = 2
    payload = {"field": "1", "field2": "2"}

    # when
    cache_key_1 = generate_cache_key_for_webhook(
        payload,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        first_app_id,
    )
    cache_key_2 = generate_cache_key_for_webhook(
        payload,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        second_app_id,
    )

    # then
    assert cache_key_1 != cache_key_2


def test_get_credit_card_info(app):
    # given
    brand = "VISA"
    last_digits = "1234"
    exp_year = "2023"
    exp_month = 1
    first_digits = "4321"

    credit_card_info = {
        "brand": brand,
        "lastDigits": last_digits,
        "expYear": exp_year,
        "expMonth": exp_month,
        "firstDigits": first_digits,
    }

    # when
    response = get_credit_card_info(app, credit_card_info)

    # then
    assert response.brand == brand
    assert response.last_digits == last_digits
    assert response.exp_year == int(exp_year)
    assert response.exp_month == exp_month
    assert response.first_digits == first_digits


def test_get_credit_card_info_without_first_digits_field(app):
    # given
    brand = "VISA"
    last_digits = "1234"
    exp_year = 2023
    exp_month = 1

    credit_card_info = {
        "brand": brand,
        "lastDigits": last_digits,
        "expYear": exp_year,
        "expMonth": exp_month,
    }

    # when
    response = get_credit_card_info(app, credit_card_info)

    # then
    assert response.brand == brand
    assert response.last_digits == last_digits
    assert response.exp_year == exp_year
    assert response.exp_month == exp_month
    assert response.first_digits is None


@pytest.mark.parametrize(
    "field",
    [
        "brand",
        "lastDigits",
        "expYear",
        "expMonth",
    ],
)
def test_get_credit_card_info_missing_required_field(field, app):
    # given
    brand = "VISA"
    last_digits = "1234"
    exp_year = 2023
    exp_month = 1
    first_digits = "4321"

    credit_card_info = {
        "brand": brand,
        "lastDigits": last_digits,
        "expYear": exp_year,
        "expMonth": exp_month,
        "firstDigits": first_digits,
    }
    del credit_card_info[field]

    # when
    response = get_credit_card_info(app, credit_card_info)

    # then
    assert response is None


@pytest.mark.parametrize(
    "field",
    [
        "brand",
        "lastDigits",
        "expYear",
        "expMonth",
    ],
)
def test_get_credit_card_info_required_field_is_none(field, app):
    # given
    brand = "VISA"
    last_digits = "1234"
    exp_year = 2023
    exp_month = 1
    first_digits = "4321"

    credit_card_info = {
        "brand": brand,
        "lastDigits": last_digits,
        "expYear": exp_year,
        "expMonth": exp_month,
        "firstDigits": first_digits,
    }
    credit_card_info[field] = None

    # when
    response = get_credit_card_info(app, credit_card_info)

    # then
    assert response is None


@pytest.mark.parametrize("exp_year", [None, "", "str"])
def test_get_credit_card_info_incorrect_exp_year(exp_year, app):
    # given
    brand = "VISA"
    last_digits = "1234"
    exp_month = 1
    first_digits = "4321"

    credit_card_info = {
        "brand": brand,
        "lastDigits": last_digits,
        "expYear": exp_year,
        "expMonth": exp_month,
        "firstDigits": first_digits,
    }

    # when
    response = get_credit_card_info(app, credit_card_info)

    # then
    assert response is None


@pytest.mark.parametrize("exp_month", [None, "", "str"])
def test_get_credit_card_info_incorrect_exp_month(exp_month, app):
    # given
    brand = "VISA"
    last_digits = "1234"
    exp_year = 2023
    first_digits = "4321"

    credit_card_info = {
        "brand": brand,
        "lastDigits": last_digits,
        "expYear": exp_year,
        "expMonth": exp_month,
        "firstDigits": first_digits,
    }

    # when
    response = get_credit_card_info(app, credit_card_info)

    # then
    assert response is None


def test_get_payment_method_from_response(payment_method_response, app):
    # when
    payment_method = get_payment_method_from_response(
        app, payment_method_response, "usd"
    )

    # then
    assert payment_method.id == to_payment_app_id(app, payment_method_response["id"])
    assert payment_method.external_id == payment_method_response["id"]
    assert payment_method.type == payment_method_response["type"]
    assert payment_method.gateway == PaymentGateway(
        id=app.identifier, name=app.name, currencies=["usd"], config=[]
    )
    assert payment_method.supported_payment_flows == [
        flow.lower() for flow in payment_method_response["supportedPaymentFlows"]
    ]
    assert payment_method.credit_card_info == get_credit_card_info(
        app, payment_method_response["creditCardInfo"]
    )
    assert payment_method.name == payment_method_response["name"]
    assert payment_method.data == payment_method_response["data"]


@pytest.mark.parametrize("field", ["id", "type", "supportedPaymentFlows"])
def test_get_payment_method_from_response_missing_required_field(
    field, payment_method_response, app
):
    # given
    del payment_method_response[field]

    # when
    payment_method = get_payment_method_from_response(
        app, payment_method_response, "usd"
    )

    # then
    assert payment_method is None


@pytest.mark.parametrize("field", ["creditCardInfo", "name", "data"])
def test_get_payment_method_from_response_optional_field(
    field, payment_method_response, app
):
    del payment_method_response[field]

    # when
    payment_method = get_payment_method_from_response(
        app, payment_method_response, "usd"
    )

    # then
    assert payment_method.id == to_payment_app_id(app, payment_method_response["id"])
    assert payment_method.external_id == payment_method_response["id"]
    assert payment_method.type == payment_method_response["type"]
    assert payment_method.gateway == PaymentGateway(
        id=app.identifier, name=app.name, currencies=["usd"], config=[]
    )
    assert payment_method.supported_payment_flows == [
        flow.lower() for flow in payment_method_response["supportedPaymentFlows"]
    ]


@pytest.mark.parametrize("field", ["id", "type", "supportedPaymentFlows"])
def test_get_payment_method_from_response_required_field_is_none(
    field, payment_method_response, app
):
    # given
    payment_method_response[field] = None

    # when
    payment_method = get_payment_method_from_response(
        app, payment_method_response, "usd"
    )

    # then
    assert payment_method is None


def test_get_payment_method_from_response_incorrect_payment_flow_choices(
    payment_method_response, app
):
    # given
    payment_method_response["supportedPaymentFlows"] = ["incorrect", "INTERACTIVE"]

    # when
    payment_method = get_payment_method_from_response(
        app, payment_method_response, "usd"
    )

    # then
    assert payment_method is None


def test_get_list_stored_payment_methods_from_response(payment_method_response, app):
    # given
    second_payment_method = copy.deepcopy(payment_method_response)
    del second_payment_method["id"]
    list_stored_payment_methods_response = {
        "paymentMethods": [payment_method_response, second_payment_method]
    }

    # when
    response = get_list_stored_payment_methods_from_response(
        app, list_stored_payment_methods_response, "usd"
    )

    # then
    assert len(response) == 1
    assert response == [
        get_payment_method_from_response(app, payment_method_response, "usd")
    ]
