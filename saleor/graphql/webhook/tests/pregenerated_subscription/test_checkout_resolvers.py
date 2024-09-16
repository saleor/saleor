import datetime
from unittest import mock

from django.test import override_settings
from django.utils import timezone

from .....shipping.models import ShippingMethod
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_total_price_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)
    checkout_total_price_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                totalPrice {
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = tax_data_response

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_subtotal_price_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)
    checkout_total_price_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                subtotalPrice {
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = tax_data_response

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_total_balance_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)
    checkout_total_price_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                totalBalance {
                    amount
                }
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = tax_data_response

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_shipping_price_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)
    checkout_total_price_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                shippingPrice {
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                    tax {
                        amount
                    }
                }
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = tax_data_response

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_authorize_status_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)
    checkout_total_price_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                authorizeStatus
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = tax_data_response

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_charge_status_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)
    checkout_total_price_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                chargeStatus
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = tax_data_response

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_line_unit_price_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout_with_item,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    checkout_with_item.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout_with_item.save()
    checkout_global_id = to_global_id_or_none(checkout_with_item)
    checkout_total_price_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                lines {
                    unitPrice {
                        net {
                            amount
                        }
                        gross {
                            amount
                        }
                        tax {
                            amount
                        }
                    }
                }
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = tax_data_response

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["checkout"]["id"] == checkout_global_id
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_line_total_price_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout_with_item,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    checkout_with_item.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout_with_item.save()
    checkout_global_id = to_global_id_or_none(checkout_with_item)
    checkout_total_price_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                lines {
                    totalPrice {
                        net {
                            amount
                        }
                        gross {
                            amount
                        }
                        tax {
                            amount
                        }
                    }
                }
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = tax_data_response

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["checkout"]["id"] == checkout_global_id
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_shipping_methods_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout_with_shipping_address,
    shipping_method,
    api_client,
    exclude_shipping_app_with_subscription,
):
    # given
    checkout = checkout_with_shipping_address
    checkout_global_id = to_global_id_or_none(checkout)
    shipping_methods = ShippingMethod.objects.order_by("id").all()
    shipping_method_global_ids = [
        to_global_id_or_none(shipping_method) for shipping_method in shipping_methods
    ]
    exclude_msg = "Shipping method is excluded via metadata by external app."
    checkout_shipping_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                shippingMethods {
                    id
                    name
                    active
                    message
                }
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = {
        "excluded_methods": [
            {
                "id": shipping_method_global_ids[1],
                "reason": exclude_msg,
            },
        ]
    }

    # when
    response = api_client.post_graphql(checkout_shipping_query, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["checkout"]["id"] == checkout_global_id
    assert content["data"]["checkout"]["shippingMethods"] == [
        {
            "id": shipping_method_global_ids[0],
            "name": "DHL",
            "active": True,
            "message": "",
        },
        {
            "id": shipping_method_global_ids[1],
            "name": "DHL",
            "active": False,
            "message": exclude_msg,
        },
    ]
    mock_request.assert_called_once()
    mock_generate_payload.assert_not_called()


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_available_shipping_methods_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout_with_shipping_address,
    shipping_method,
    api_client,
    exclude_shipping_app_with_subscription,
):
    # given
    checkout = checkout_with_shipping_address
    checkout_global_id = to_global_id_or_none(checkout)
    shipping_methods = ShippingMethod.objects.order_by("id").all()
    shipping_method_global_ids = [
        to_global_id_or_none(shipping_method) for shipping_method in shipping_methods
    ]
    exclude_msg = "Shipping method is excluded via metadata by external app."
    checkout_shipping_query = """
        query getCheckout($id: ID!) {
            checkout(id: $id) {
                id
                availableShippingMethods {
                    id
                    name
                    active
                    message
                }
            }
        }
    """
    variables = {"id": checkout_global_id}

    mock_request.return_value = {
        "excluded_methods": [
            {
                "id": shipping_method_global_ids[1],
                "reason": exclude_msg,
            },
        ]
    }

    # when
    response = api_client.post_graphql(checkout_shipping_query, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["checkout"]["id"] == checkout_global_id
    assert content["data"]["checkout"]["availableShippingMethods"] == [
        {
            "id": shipping_method_global_ids[0],
            "name": "DHL",
            "active": True,
            "message": "",
        }
    ]
    mock_request.assert_called_once()
    mock_generate_payload.assert_not_called()
