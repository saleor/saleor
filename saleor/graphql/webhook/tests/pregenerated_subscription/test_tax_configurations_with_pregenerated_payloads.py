import datetime
from collections import defaultdict
from unittest import mock

from django.test import override_settings
from django.utils import timezone

from .....checkout.calculations import fetch_checkout_data
from .....tax import TaxCalculationStrategy
from .....tax.models import TaxConfiguration
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_pregenerated_payload_with_selected_tax_app_price_entered_with_tax(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    tax_app_global_id = to_global_id_or_none(tax_app)
    tax_configuration = TaxConfiguration.objects.get()
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.tax_app_id = tax_app_global_id
    tax_configuration.save()
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
def test_pregenerated_payload_with_selected_tax_app_price_entered_without_tax(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    tax_app_global_id = to_global_id_or_none(tax_app)
    tax_configuration = TaxConfiguration.objects.get()
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.prices_entered_with_tax = False
    tax_configuration.tax_app_id = tax_app_global_id
    tax_configuration.save()
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
def test_pregenerated_payload_with_selected_external_tax_app_price_entered_without_tax(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    external_tax_app,
):
    # given
    tax_configuration = TaxConfiguration.objects.get()
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.prices_entered_with_tax = False
    tax_configuration.tax_app_id = external_tax_app.identifier
    tax_configuration.save()
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
def test_pregenerated_payload_with_selected_external_tax_app_price_entered_with_tax(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    external_tax_app,
):
    # given
    tax_configuration = TaxConfiguration.objects.get()
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.tax_app_id = external_tax_app.identifier
    tax_configuration.save()
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
def test_pregenerated_payload_with_all_apps_price_entered_with_tax(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
    external_tax_app,
):
    # given
    tax_configuration = TaxConfiguration.objects.get()
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save()
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

    # Set response for tax calculation to None to ensure that all apps are called
    mock_request.return_value = None

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    assert mock_request.call_count == 2
    assert content["data"]["checkout"]["id"] == checkout_global_id


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_pregenerated_payload_with_all_apps_price_entered_without_tax(
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
    external_tax_app,
):
    # given
    tax_configuration = TaxConfiguration.objects.get()
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.prices_entered_with_tax = False
    tax_configuration.save()
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

    # Set response for tax calculation to None to ensure that all apps are called
    mock_request.return_value = None

    # when
    response = api_client.post_graphql(checkout_total_price_query, variables)
    content = get_graphql_content(response)

    # then
    mock_generate_payload.assert_not_called()
    assert mock_request.call_count == 2
    assert content["data"]["checkout"]["id"] == checkout_global_id


@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
@mock.patch(
    "saleor.checkout.calculations.fetch_checkout_data",
    wraps=fetch_checkout_data,
)
def test_pregenerated_payload_skipped_when_checkout_not_expired(
    mock_fetch_checkout_data,
    mock_generate_payload,
    mock_request,
    checkout,
    api_client,
    tax_data_response,
    tax_app,
):
    # given
    tax_app_global_id = to_global_id_or_none(tax_app)
    tax_configuration = TaxConfiguration.objects.get()
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.tax_app_id = tax_app_global_id
    tax_configuration.save()
    checkout.price_expiration = timezone.now() + datetime.timedelta(days=1)
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
    assert content["data"]["checkout"]["id"] == checkout_global_id
    mock_generate_payload.assert_not_called()
    mock_request.assert_not_called()
    mock_fetch_checkout_data.assert_called_once()
    assert mock_fetch_checkout_data.call_args.kwargs[
        "pregenerated_subscription_payloads"
    ] == defaultdict(dict)
