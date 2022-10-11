import pytest

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....payment import TransactionKind
from ..utils import (
    APP_ID_PREFIX,
    clear_successful_delivery,
    from_payment_app_id,
    parse_list_payment_gateways_response,
    parse_payment_action_response,
    to_payment_app_id,
)


def test_to_payment_app_id_app_identifier_used(app):
    # given
    gateway_id = "example-gateway"

    # when
    payment_app_id = to_payment_app_id(app, gateway_id)

    # then
    assert payment_app_id == f"{APP_ID_PREFIX}:{app.identifier}:{gateway_id}"


def test_to_payment_app_id_app_id_used(app):
    # given
    app.identifier = None
    app.save(update_fields=["identifier"])

    gateway_id = "example-gateway"

    # when
    payment_app_id = to_payment_app_id(app, gateway_id)

    # then
    assert payment_app_id == f"{APP_ID_PREFIX}:{app.id}:{gateway_id}"


def test_from_payment_app_id_from_pk():
    app_id = "app:1:credit-card"
    payment_app_data = from_payment_app_id(app_id)
    assert payment_app_data.app_pk == 1
    assert payment_app_data.name == "credit-card"


def test_from_payment_app_id_from_identifier(app):
    app_id = f"app:{app.identifier}:credit-card"
    payment_app_data = from_payment_app_id(app_id)
    assert payment_app_data.app_identifier == app.identifier
    assert payment_app_data.name == "credit-card"


@pytest.mark.parametrize(
    "app_id",
    [
        "",
        "::",
        "1",
        "name",
        "1:1:name",
        f"{APP_ID_PREFIX}:1",
        f"{APP_ID_PREFIX}:1:",
    ],
)
def test_from_payment_app_id_invalid(app_id):
    app_pk = from_payment_app_id(app_id)
    assert app_pk is None


def test_parse_list_payment_gateways_response_app_identifier(app):
    # given
    response_data = [
        {
            "id": "credit-card",
            "name": "Credit Card",
            "currencies": ["USD", "EUR"],
            "config": [{"field": "example-key", "value": "example-value"}],
        },
    ]

    # when
    gateways = parse_list_payment_gateways_response(response_data, app)

    # then
    assert gateways[0].id == to_payment_app_id(app, response_data[0]["id"])
    assert gateways[0].name == response_data[0]["name"]
    assert gateways[0].currencies == response_data[0]["currencies"]
    assert gateways[0].config == response_data[0]["config"]


def test_parse_list_payment_gateways_response_app_id(app):
    # given
    app.identifier = None
    app.save(update_fields=["identifier"])

    response_data = [
        {
            "id": "credit-card",
            "name": "Credit Card",
            "currencies": ["USD", "EUR"],
            "config": [{"field": "example-key", "value": "example-value"}],
        },
    ]

    # when
    gateways = parse_list_payment_gateways_response(response_data, app)

    # then
    assert gateways[0].id == to_payment_app_id(app, response_data[0]["id"])
    assert gateways[0].name == response_data[0]["name"]
    assert gateways[0].currencies == response_data[0]["currencies"]
    assert gateways[0].config == response_data[0]["config"]


def test_parse_list_payment_gateways_response_no_id(app):
    response_data = [
        {
            "name": "Credit Card",
            "currencies": ["USD", "EUR"],
        },
    ]
    gateways = parse_list_payment_gateways_response(response_data, app.id)
    assert gateways == []


def test_parse_list_payment_gateways_response_dict_response(app):
    # We expect that the response_data is a list of dicts, otherwise it won't be
    # parsed.
    response_data = {
        "id": "credit-card",
        "name": "Credit Card",
        "currencies": ["USD", "EUR"],
        "config": [{"field": "example-key", "value": "example-value"}],
    }
    gateways = parse_list_payment_gateways_response(response_data, app.id)
    assert gateways == []


@pytest.fixture
def payment_action_response(dummy_webhook_app_payment_data):
    return {
        "action_required": False,
        "action_required_data": {},
        "amount": dummy_webhook_app_payment_data.amount,
        "currency": dummy_webhook_app_payment_data.currency,
        "customer_id": "1000",
        "kind": TransactionKind.AUTH,
        "payment_method": {
            "brand": "Visa",
            "exp_month": "05",
            "exp_year": "2025",
            "last_4": "4444",
            "name": "John Doe",
            "type": "card",
        },
        "psp_reference": "1000",
        "transaction_id": "1000",
        "transaction_already_processed": False,
    }


def test_parse_payment_action_response(
    dummy_webhook_app_payment_data, payment_action_response
):
    gateway_response = parse_payment_action_response(
        dummy_webhook_app_payment_data, payment_action_response, TransactionKind.AUTH
    )
    assert gateway_response.error is None
    assert gateway_response.is_success
    assert gateway_response.raw_response == payment_action_response
    assert (
        gateway_response.action_required == payment_action_response["action_required"]
    )
    assert (
        gateway_response.action_required_data
        == payment_action_response["action_required_data"]
    )
    assert gateway_response.amount == payment_action_response["amount"]
    assert gateway_response.currency == payment_action_response["currency"]
    assert gateway_response.customer_id == payment_action_response["customer_id"]
    assert gateway_response.kind == payment_action_response["kind"]
    assert gateway_response.psp_reference == payment_action_response["psp_reference"]
    assert gateway_response.transaction_id == payment_action_response["transaction_id"]
    assert (
        gateway_response.transaction_already_processed
        == payment_action_response["transaction_already_processed"]
    )

    assert (
        gateway_response.payment_method_info.brand
        == payment_action_response["payment_method"]["brand"]
    )
    assert (
        gateway_response.payment_method_info.exp_month
        == payment_action_response["payment_method"]["exp_month"]
    )
    assert (
        gateway_response.payment_method_info.exp_year
        == payment_action_response["payment_method"]["exp_year"]
    )
    assert (
        gateway_response.payment_method_info.last_4
        == payment_action_response["payment_method"]["last_4"]
    )
    assert (
        gateway_response.payment_method_info.name
        == payment_action_response["payment_method"]["name"]
    )
    assert (
        gateway_response.payment_method_info.type
        == payment_action_response["payment_method"]["type"]
    )


def test_parse_payment_action_response_parse_amount(
    dummy_webhook_app_payment_data, payment_action_response
):
    # test amount is not a decimal, should use amount from payment information
    payment_action_response["amount"] = "boom"
    gateway_response = parse_payment_action_response(
        dummy_webhook_app_payment_data, payment_action_response, TransactionKind.AUTH
    )
    assert gateway_response.amount == dummy_webhook_app_payment_data.amount

    # test amount not in webhook response, should use amount from payment information
    del payment_action_response["amount"]
    gateway_response = parse_payment_action_response(
        dummy_webhook_app_payment_data, payment_action_response, TransactionKind.AUTH
    )
    assert gateway_response.amount == dummy_webhook_app_payment_data.amount


def test_clear_successful_delivery(event_delivery):
    # given
    assert EventDelivery.objects.filter(pk=event_delivery.pk).exists()
    event_delivery.status = EventDeliveryStatus.SUCCESS
    event_delivery.save()
    event_payload = event_delivery.payload
    # when
    clear_successful_delivery(event_delivery)
    # then
    assert not EventDelivery.objects.filter(pk=event_delivery.pk).exists()
    assert not EventPayload.objects.filter(pk=event_payload.pk).exists()


def test_clear_successful_delivery_when_payload_in_multiple_deliveries(event_delivery):
    # given
    assert EventDelivery.objects.filter(pk=event_delivery.pk).exists()
    event_delivery.status = EventDeliveryStatus.SUCCESS
    event_delivery.save()
    event_payload = event_delivery.payload
    EventDelivery.objects.create(payload=event_payload, webhook=event_delivery.webhook)
    # when
    clear_successful_delivery(event_delivery)
    # then
    assert not EventDelivery.objects.filter(pk=event_delivery.pk).exists()
    assert EventPayload.objects.filter(pk=event_payload.pk).exists()


def test_clear_successful_delivery_on_failed_delivery(event_delivery):
    # given
    event_delivery.status = EventDeliveryStatus.FAILED
    event_delivery.save()
    # when
    clear_successful_delivery(event_delivery)
    # then
    assert EventDelivery.objects.filter(pk=event_delivery.pk).exists()
