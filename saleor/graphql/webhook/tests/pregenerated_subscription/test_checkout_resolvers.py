import datetime
from unittest import mock

from django.test import override_settings
from django.utils import timezone

from .....shipping.models import ShippingMethod
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

_line_tax_data = {
    "total_gross_amount": 2.5,
    "total_net_amount": 2,
    "tax_rate": 20,
}
TAX_DATA_RESPONSE = {
    "currency": "USD",
    "shipping_price_gross_amount": 10,
    "shipping_price_net_amount": 8,
    "shipping_tax_rate": 20,
    "lines": [_line_tax_data for _ in range(4)],
}


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_total_price_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout_with_shipping_address,
    api_client,
    tax_app,
):
    # given
    checkout = checkout_with_shipping_address
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

    mock_request.return_value = TAX_DATA_RESPONSE

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id
    assert content["data"]["checkout"]["totalPrice"]["net"]["amount"] == 16
    assert content["data"]["checkout"]["totalPrice"]["gross"]["amount"] == 20


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_subtotal_price_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout_with_shipping_address,
    api_client,
    tax_app,
):
    # given
    checkout = checkout_with_shipping_address
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

    mock_request.return_value = TAX_DATA_RESPONSE

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id
    assert content["data"]["checkout"]["subtotalPrice"]["net"]["amount"] == 8
    assert content["data"]["checkout"]["subtotalPrice"]["gross"]["amount"] == 10


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_total_balance_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout_with_shipping_address,
    api_client,
    tax_app,
):
    # given
    checkout = checkout_with_shipping_address
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

    mock_request.return_value = TAX_DATA_RESPONSE

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id
    assert content["data"]["checkout"]["totalBalance"]["amount"] == -20


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_shipping_price_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout_with_shipping_address,
    api_client,
    tax_app,
):
    # given
    checkout = checkout_with_shipping_address
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

    mock_request.return_value = TAX_DATA_RESPONSE

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert content["data"]["checkout"]["id"] == checkout_global_id
    assert content["data"]["checkout"]["shippingPrice"]["net"]["amount"] == 8
    assert content["data"]["checkout"]["shippingPrice"]["gross"]["amount"] == 10


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_checkout_authorize_status_use_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    checkout_with_shipping_address,
    api_client,
    tax_app,
):
    # given
    checkout = checkout_with_shipping_address
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

    mock_request.return_value = TAX_DATA_RESPONSE

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
    checkout_with_shipping_address,
    api_client,
    tax_app,
):
    # given
    checkout = checkout_with_shipping_address
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

    mock_request.return_value = TAX_DATA_RESPONSE

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
    checkout_with_shipping_address,
    api_client,
    tax_app,
):
    # given
    checkout = checkout_with_shipping_address
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)
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

    mock_request.return_value = TAX_DATA_RESPONSE

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["checkout"]["id"] == checkout_global_id
    lines_data = content["data"]["checkout"]["lines"]
    assert lines_data[0]["unitPrice"]["net"]["amount"] == 2
    assert lines_data[0]["unitPrice"]["gross"]["amount"] == 2.5
    assert lines_data[1]["unitPrice"]["net"]["amount"] == 0.2
    assert lines_data[1]["unitPrice"]["gross"]["amount"] == 0.25
    assert lines_data[2]["unitPrice"]["net"]["amount"] == 0.67
    assert lines_data[2]["unitPrice"]["gross"]["amount"] == 0.83
    assert lines_data[3]["unitPrice"]["net"]["amount"] == 0.4
    assert lines_data[3]["unitPrice"]["gross"]["amount"] == 0.5
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
    checkout_with_shipping_address,
    api_client,
    tax_app,
):
    # given
    checkout = checkout_with_shipping_address
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)
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

    mock_request.return_value = TAX_DATA_RESPONSE

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["checkout"]["id"] == checkout_global_id
    for line_data in content["data"]["checkout"]["lines"]:
        assert line_data["totalPrice"]["net"]["amount"] == 2
        assert line_data["totalPrice"]["gross"]["amount"] == 2.5
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


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_webhook_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_shipping_methods_and_taxes_use_pregenerated_payload(
    mock_generate_payload,
    mock_shipping_request,
    mock_tax_request,
    checkout_with_shipping_address,
    shipping_method,
    api_client,
    exclude_shipping_app_with_subscription,
    tax_data_response,
    tax_app,
):
    # given
    checkout = checkout_with_shipping_address
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
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
                totalPrice {
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
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

    mock_shipping_request.return_value = {
        "excluded_methods": [
            {
                "id": shipping_method_global_ids[1],
                "reason": exclude_msg,
            },
        ]
    }
    mock_tax_request.return_value = TAX_DATA_RESPONSE

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
    assert content["data"]["checkout"]["totalPrice"]["net"]["amount"] == 16
    assert content["data"]["checkout"]["totalPrice"]["gross"]["amount"] == 20
    mock_tax_request.assert_called_once()
    mock_shipping_request.assert_called_once()
    mock_generate_payload.assert_not_called()


CHECKOUTS_QUERY = """
 query CheckoutsQuery {
   checkouts(first: 1) {
     edges {
       node {
         id
         deliveryMethod {
           __typename
           ... on ShippingMethod {
             id
             name
             price {
               amount
             }
           }
         }
         shippingPrice {
           gross {
             amount
           }
         }
         totalPrice {
           gross {
             amount
           }
         }
         subtotalPrice {
           gross {
             amount
           }
         }
         lines {
           totalPrice {
             gross {
               amount
             }
           }
           unitPrice {
             gross {
               amount
             }
           }
         }
         shippingMethods {
           id
           name
           active
         }
         availableShippingMethods {
           id
           name
           active
         }
       }
     }
   }
 }
 """


@mock.patch(
    "saleor.graphql.checkout.types.PregeneratedCheckoutTaxPayloadsByCheckoutTokenLoader"
)
def test_pregegenerated_tax_payload_is_skipped_for_bulk_queries(
    mocked_pregenerated_payload,
    checkout_with_shipping_address,
    staff_api_client,
    permission_manage_checkouts,
):
    # given
    checkout = checkout_with_shipping_address
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)

    # when
    response = staff_api_client.post_graphql(
        CHECKOUTS_QUERY,
        permissions=[permission_manage_checkouts],
    )
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["checkouts"]["edges"]) == 1
    checkout = content["data"]["checkouts"]["edges"][0]["node"]
    assert checkout["id"] == checkout_global_id

    mocked_pregenerated_payload.assert_not_called()


@mock.patch(
    "saleor.graphql.checkout.types."
    "PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader"
)
def test_pregegenerated_exclude_shipping_payload_is_skipped_for_bulk_queries(
    mocked_pregenerated_payload,
    checkout_with_shipping_address,
    staff_api_client,
    permission_manage_checkouts,
):
    # given
    checkout = checkout_with_shipping_address
    checkout.price_expiration = timezone.now() - datetime.timedelta(days=1)
    checkout.save()
    checkout_global_id = to_global_id_or_none(checkout)

    # when
    response = staff_api_client.post_graphql(
        CHECKOUTS_QUERY,
        permissions=[permission_manage_checkouts],
    )
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["checkouts"]["edges"]) == 1
    checkout = content["data"]["checkouts"]["edges"][0]["node"]
    assert checkout["id"] == checkout_global_id

    mocked_pregenerated_payload.assert_not_called()
