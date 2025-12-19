from unittest.mock import ANY, patch

import graphene
from django.test import override_settings

from .....core.models import EventDelivery
from .....order import OrderStatus
from .....order.actions import call_order_event
from .....order.error_codes import OrderErrorCode
from .....order.models import Order
from .....product.models import ProductVariant
from .....tests import race_condition
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import snake_to_camel_case
from ....tests.utils import assert_no_permission, get_graphql_content
from ...mutations.order_update import OrderUpdateInput

ORDER_UPDATE_MUTATION = """
    mutation orderUpdate(
        $id: ID!, $input: OrderUpdateInput!
    ) {
        orderUpdate(
            id: $id,
            input: $input,
            ) {
            errors {
                field
                code
            }
            order {
                userEmail
                externalReference
                metadata {key, value}
                privateMetadata {key, value}
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    external_reference = "test-ext-ref"

    variables = {
        "id": order_id,
        "input": {
            "userEmail": email,
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
            "externalReference": external_reference,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email
    assert data["externalReference"] == external_reference

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.shipping_address.validation_skipped is False
    assert order.billing_address.validation_skipped is False
    assert order.draft_save_billing_address is None
    assert order.draft_save_shipping_address is None
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED
    assert order.external_reference == external_reference
    order_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


def test_order_update_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    order_with_lines,
    graphql_address_data,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = order_with_lines

    order.user = None
    order.channel = channel_PLN
    order.save(update_fields=["channel", "user"])

    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    external_reference = "test-ext-ref"

    variables = {
        "id": order_id,
        "input": {
            "userEmail": email,
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
            "externalReference": external_reference,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_by_app(
    order_updated_webhook_mock,
    app_api_client,
    permission_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    external_reference = "test-ext-ref"

    variables = {
        "id": order_id,
        "input": {
            "userEmail": email,
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
            "externalReference": external_reference,
        },
    }

    # when
    response = app_api_client.post_graphql(
        ORDER_UPDATE_MUTATION, variables, permissions=(permission_manage_orders,)
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email
    assert data["externalReference"] == external_reference

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED
    assert order.external_reference == external_reference
    order_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_with_draft_order(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    graphql_address_data,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.user = None
    order.save()
    email = "not_default@example.com"
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {
        "id": order_id,
        "input": {
            "userEmail": email,
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
        },
    }
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    error = content["data"]["orderUpdate"]["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == OrderErrorCode.INVALID.name
    order_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_without_sku(
    plugin_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    ProductVariant.objects.update(sku=None)
    order_with_lines.lines.update(product_sku=None)

    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {
        "id": order_id,
        "input": {
            "userEmail": email,
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
        },
    }
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED
    assert plugin_mock.called is True


def test_order_update_anonymous_user_no_user_email(
    staff_api_client,
    order_with_lines,
    permission_group_manage_orders,
    graphql_address_data,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.user = None
    order.save()
    query = """
            mutation orderUpdate(
            $id: ID!, $address: AddressInput) {
                orderUpdate(
                    id: $id, input: {
                        shippingAddress: $address,
                        billingAddress: $address}) {
                    errors {
                        field
                        message
                    }
                    order {
                        id
                    }
                }
            }
            """
    first_name = "Test fname"
    last_name = "Test lname"
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "address": graphql_address_data}
    response = staff_api_client.post_graphql(query, variables)
    get_graphql_content(response)
    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name != first_name
    assert order.billing_address.last_name != last_name
    assert order.status == OrderStatus.UNFULFILLED


def test_order_update_user_email_existing_user(
    staff_api_client,
    order_with_lines,
    customer_user,
    permission_group_manage_orders,
    graphql_address_data,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.user = None
    order.save()
    query = """
        mutation orderUpdate(
        $id: ID!, $email: String, $address: AddressInput) {
            orderUpdate(
                id: $id, input: {
                    userEmail: $email, shippingAddress: $address,
                    billingAddress: $address}) {
                errors {
                    field
                    message
                }
                order {
                    userEmail
                }
            }
        }
        """
    email = customer_user.email
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "address": graphql_address_data, "email": email}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user == customer_user


ORDER_UPDATE_BY_EXTERNAL_REFERENCE = """
    mutation orderUpdate(
        $id: ID
        $externalReference: String
        $input: OrderUpdateInput!
    ) {
        orderUpdate(
            id: $id
            externalReference: $externalReference
            input: $input
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
                externalReference
                shippingAddress {
                    firstName
                }
            }
        }
    }
    """


def test_order_update_by_external_reference(
    staff_api_client, permission_group_manage_orders, order, graphql_address_data
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    ext_ref = "test-ext-ref"
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])

    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    variables = {
        "externalReference": ext_ref,
        "input": {"shippingAddress": graphql_address_data},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderUpdate"]
    assert not data["errors"]
    assert data["order"]["externalReference"] == ext_ref
    assert data["order"]["id"] == graphene.Node.to_global_id("Order", order.id)
    assert (
        data["order"]["shippingAddress"]["firstName"]
        == graphql_address_data["firstName"]
    )
    order.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]


def test_order_update_by_both_id_and_external_reference(
    staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    variables = {
        "id": "test-id",
        "externalReference": "test-ext-ref",
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderUpdate"]
    assert not data["order"]
    assert (
        data["errors"][0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_order_update_by_external_reference_not_existing(
    staff_api_client, permission_group_manage_orders, voucher_free_shipping
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_BY_EXTERNAL_REFERENCE
    ext_ref = "non-existing-ext-ref"
    variables = {
        "externalReference": ext_ref,
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderUpdate"]
    assert not data["order"]
    assert data["errors"][0]["message"] == f"Couldn't resolve to a node: {ext_ref}"


def test_order_update_with_non_unique_external_reference(
    staff_api_client, permission_group_manage_orders, order, order_list
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    ext_ref = "test-ext-ref"
    order_1 = order_list[0]
    order_1.external_reference = ext_ref
    order_1.save(update_fields=["external_reference"])
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {"id": order_id, "input": {"externalReference": ext_ref}}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["orderUpdate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == OrderErrorCode.UNIQUE.name
    assert error["message"] == "Order with this External reference already exists."


ORDER_UPDATE_MUTATION_WITH_ADDRESS = """
    mutation orderUpdate($id: ID!, $address: AddressInput) {
        orderUpdate(
            id: $id,
            input: {
                shippingAddress: $address,
                billingAddress: $address
                }
            ) {
            errors {
                field
                code
            }
            order {
                shippingAddress {
                    postalCode
                }
                billingAddress {
                    postalCode
                }
            }
        }
    }
"""


def test_order_update_invalid_address_skip_validation(
    staff_api_client,
    permission_group_manage_orders,
    order,
    graphql_address_data_skipped_validation,
):
    # given
    address_data = graphql_address_data_skipped_validation
    invalid_postal_code = "invalid_postal_code"
    address_data["postalCode"] = invalid_postal_code
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = ORDER_UPDATE_MUTATION_WITH_ADDRESS
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {"id": order_id, "address": address_data}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderUpdate"]
    assert not data["errors"]
    assert data["order"]["shippingAddress"]["postalCode"] == invalid_postal_code
    assert data["order"]["billingAddress"]["postalCode"] == invalid_postal_code
    order.refresh_from_db()
    assert order.shipping_address.postal_code == invalid_postal_code
    assert order.shipping_address.validation_skipped is True
    assert order.billing_address.postal_code == invalid_postal_code
    assert order.billing_address.validation_skipped is True


@patch(
    "saleor.graphql.order.mutations.order_update.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_order_update_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
    settings,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        order_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.ORDER_UPDATED)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]

    # confirm that event delivery was generated for each async webhook.
    order_delivery = EventDelivery.objects.get(webhook_id=order_webhook.id)
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_delivery.id, "telemetry_context": ANY},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        MessageGroupId="example.com:saleorappadditional",
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(webhook_id=order_webhook.id).exists()

    tax_delivery_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )

    assert wrapped_call_order_event.called


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_only_metadata_legacy_webhook_emission_on(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_with_lines.metadata = {}
    order_with_lines.private_metadata = {}
    order.save()
    updated_at_before = order.updated_at

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "metadata": [{"key": "meta key", "value": "meta value"}],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]

    order.refresh_from_db()

    assert order.metadata == {"meta key": "meta value"}
    assert order.updated_at > updated_at_before

    order_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_metadata_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_only_metadata_legacy_webhook_emission_off(
    order_updated_webhook_mock,
    order_metadata_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_with_lines.metadata = {}
    order_with_lines.private_metadata = {}
    order.save()
    updated_at_before = order.updated_at

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "metadata": [{"key": "meta key", "value": "meta value"}],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]

    order.refresh_from_db()

    assert order.metadata == {"meta key": "meta value"}
    assert order.updated_at > updated_at_before

    order_updated_webhook_mock.assert_not_called()
    order_metadata_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_metadata_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_only_private_metadata_legacy_webhook_emission_on(
    order_updated_webhook_mock,
    order_metadata_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_with_lines.metadata = {}
    order_with_lines.private_metadata = {}
    order.save()
    updated_at_before = order.updated_at

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "privateMetadata": [{"key": "meta key", "value": "meta value"}],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]

    order.refresh_from_db()

    assert order.private_metadata == {"meta key": "meta value"}
    assert order.updated_at > updated_at_before

    order_updated_webhook_mock.assert_called_once_with(order, webhooks=set())
    order_metadata_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_metadata_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_only_private_metadata_legacy_webhook_emission_off(
    order_updated_webhook_mock,
    order_metadata_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_with_lines.metadata = {}
    order_with_lines.private_metadata = {}
    order.save()
    updated_at_before = order.updated_at

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "privateMetadata": [{"key": "meta key", "value": "meta value"}],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]

    order.refresh_from_db()

    assert order.private_metadata == {"meta key": "meta value"}
    assert order.updated_at > updated_at_before

    order_updated_webhook_mock.assert_not_called()
    order_metadata_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_metadata_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_public_and_private_metadata_legacy_webhook_emission_on(
    order_updated_webhook_mock,
    order_metadata_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_with_lines.metadata = {}
    order_with_lines.private_metadata = {}
    order.save()
    updated_at_before = order.updated_at

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "privateMetadata": [{"key": "meta key", "value": "meta value"}],
            "metadata": [{"key": "meta key", "value": "meta value"}],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]

    order.refresh_from_db()

    assert order.metadata == {"meta key": "meta value"}
    assert order.private_metadata == {"meta key": "meta value"}
    assert order.updated_at > updated_at_before

    order_updated_webhook_mock.assert_called_once_with(order, webhooks=set())
    order_metadata_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_metadata_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_public_and_private_metadata_legacy_webhook_emission_off(
    order_updated_webhook_mock,
    order_metadata_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_with_lines.metadata = {}
    order_with_lines.private_metadata = {}
    order.save()
    updated_at_before = order.updated_at

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "privateMetadata": [{"key": "meta key", "value": "meta value"}],
            "metadata": [{"key": "meta key", "value": "meta value"}],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]

    order.refresh_from_db()

    assert order.metadata == {"meta key": "meta value"}
    assert order.private_metadata == {"meta key": "meta value"}
    assert order.updated_at > updated_at_before

    order_updated_webhook_mock.assert_not_called()
    order_metadata_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


@patch("saleor.plugins.manager.PluginsManager.order_metadata_updated")
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_invalid_metadata(
    order_updated_webhook_mock,
    order_metadata_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_with_lines.metadata = {}
    order_with_lines.private_metadata = {}
    order.save()
    updated_at_before = order.updated_at

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            # Empty key is invalid
            "metadata": [{"key": "", "value": "meta value"}],
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["orderUpdate"]["errors"]

    assert errors[0]["field"] == "metadata"
    assert errors[0]["code"] == "REQUIRED"

    order.refresh_from_db()
    assert order.metadata == {}
    assert order.updated_at == updated_at_before

    order_updated_webhook_mock.assert_not_called()
    order_metadata_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_empty_input(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]
    assert not data["errors"]

    order_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_nothing_changed(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.external_reference = "test-ext-ref"
    order.save(update_fields=["external_reference"])

    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "externalReference": order.external_reference,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]
    assert not data["errors"]

    order_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_update_with_language_code(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    order.user = None
    order.save()
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {"languageCode": "PL"},
    }

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]

    order.refresh_from_db()
    assert order.language_code == "pl"
    order_updated_webhook_mock.assert_called_once_with(order, webhooks=set())


@patch(
    "saleor.graphql.order.mutations.order_update.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.graphql.order.mutations.order_update.OrderUpdate._save_order_instance")
def test_order_update_no_changes(
    save_order_mock,
    call_event_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    address,
):
    # given
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)

    key = "some_key"
    value = "some_value"
    address.metadata = {key: value}
    address.save(update_fields=["metadata"])

    order.metadata = {key: value}
    order.private_metadata = {key: value}
    order.shipping_address = address
    order.billing_address = address
    order.external_reference = "some_reference_string"
    order.language_code = "pl"
    order.save()

    address_input = {
        snake_to_camel_case(key): value for key, value in address.as_data().items()
    }
    address_input["metadata"] = [{"key": key, "value": value}]
    address_input.pop("privateMetadata")
    skip_validation = address_input.pop("validationSkipped")
    address_input["skipValidation"] = skip_validation

    input_fields = [
        snake_to_camel_case(key) for key in OrderUpdateInput._meta.fields.keys()
    ]

    input = {
        "billingAddress": address_input,
        "shippingAddress": address_input,
        "userEmail": order.user_email,
        "externalReference": order.external_reference,
        "metadata": [{"key": key, "value": value}],
        "privateMetadata": [{"key": key, "value": value}],
        "languageCode": "PL",
    }
    assert set(input_fields) == set(input.keys())

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"id": order_id, "input": input}

    # when
    response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    order.refresh_from_db()
    save_order_mock.assert_not_called()
    call_event_mock.assert_not_called()


@patch(
    "saleor.graphql.order.mutations.order_update.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.graphql.order.mutations.order_update.OrderUpdate._save_order_instance")
def test_order_update_emit_events(
    save_order_mock,
    call_event_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)

    meta_key = "some_key"
    meta_value = "some_value"
    order.metadata = {meta_key: meta_value}
    order.private_metadata = {meta_key: meta_value}
    order.customer_note = "some note"
    order.redirect_url = "https://www.example.com"
    order.external_reference = "some_reference_string"
    order.language_code = "de"
    order.save()

    input_fields = [
        snake_to_camel_case(key) for key in OrderUpdateInput._meta.fields.keys()
    ]
    # metadata fields are tested separately, updated atomically in `update_meta_fields`
    input_fields.remove("metadata")
    input_fields.remove("privateMetadata")

    assert graphql_address_data["lastName"] != order.shipping_address.last_name
    assert graphql_address_data["lastName"] != order.billing_address.last_name

    input = {
        "billingAddress": graphql_address_data,
        "shippingAddress": graphql_address_data,
        "userEmail": "new_" + order.user_email,
        "externalReference": order.external_reference + "_new",
        "languageCode": "PL",
    }
    assert set(input_fields) == set(input.keys())

    # fields making changes to related models (other than order)
    non_base_model_fields = ["billingAddress", "shippingAddress"]
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    for key, value in input.items():
        variables = {"id": order_id, "input": {key: value}}

        # when
        response = staff_api_client.post_graphql(
            ORDER_UPDATE_MUTATION,
            variables,
        )
        content = get_graphql_content(response)

        # then
        assert not content["data"]["orderUpdate"]["errors"]
        if key not in non_base_model_fields:
            save_order_mock.assert_called()
            save_order_mock.reset_mock()
        call_event_mock.assert_called()
        call_event_mock.reset_mock()


@patch(
    "saleor.graphql.order.mutations.order_update.call_order_event",
    wraps=call_order_event,
)
def test_order_update_address_not_set(
    call_event_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    order = order_with_lines
    order.shipping_address = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "billing_address"])

    order_id = graphene.Node.to_global_id("Order", order.id)

    input = {
        "billingAddress": graphql_address_data,
        "shippingAddress": graphql_address_data,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"id": order_id, "input": input}

    # when
    response = staff_api_client.post_graphql(
        ORDER_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["orderUpdate"]["errors"]
    order.refresh_from_db()
    assert order.shipping_address
    assert order.billing_address
    call_event_mock.assert_called()


def test_update_public_metadata_another_key_deleted_in_meantime(
    staff_api_client, order, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    key_1 = "public_key"
    key_2 = "another_public_key"
    value_1 = "public_value"
    value_2 = "another_public_value"
    new_value = "updated_value"

    order.metadata = {key_1: value_1, key_2: value_2}
    order.private_metadata = {key_1: value_2, key_2: value_1}
    order.save(update_fields=["metadata", "private_metadata"])

    order_id = graphene.Node.to_global_id("Order", order.pk)

    def delete_metadata(*args, **kwargs):
        order_to_update = Order.objects.get(pk=order.pk)
        order_to_update.delete_value_from_metadata(key_2)
        order_to_update.delete_value_from_private_metadata(key_1)
        order_to_update.save(update_fields=["metadata", "private_metadata"])

    variables = {
        "id": order_id,
        "input": {
            "metadata": [{"key": key_1, "value": new_value}],
            "privateMetadata": [{"key": key_2, "value": new_value}],
        },
    }
    # when
    with race_condition.RunBefore(
        "saleor.graphql.order.mutations.order_update.update_meta_fields",
        delete_metadata,
    ):
        response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orderUpdate"]["order"]
    assert order_data
    assert not content["data"]["orderUpdate"]["errors"]
    assert order_data["metadata"] == [{"key": key_1, "value": new_value}]
    assert order_data["privateMetadata"] == [{"key": key_2, "value": new_value}]

    order.refresh_from_db()

    assert order.metadata == {key_1: new_value}
    assert order.private_metadata == {key_2: new_value}


def test_update_public_metadata_another_key_updated_in_meantime(
    staff_api_client, order, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    key_1 = "public_key"
    key_2 = "another_public_key"
    value_1 = "public_value"
    value_2 = "another_public_value"
    new_value = "updated_value"
    value_changed_in_meantime = "value_changed_in_meantime"

    order.metadata = {key_1: value_1, key_2: value_2}
    order.private_metadata = {key_1: value_2, key_2: value_1}
    order.save(update_fields=["metadata", "private_metadata"])

    order_id = graphene.Node.to_global_id("Order", order.pk)

    def update_metadata(*args, **kwargs):
        order_to_update = Order.objects.get(pk=order.pk)
        order_to_update.store_value_in_metadata({key_2: value_changed_in_meantime})
        order_to_update.store_value_in_private_metadata(
            {key_1: value_changed_in_meantime}
        )
        order_to_update.save(update_fields=["metadata", "private_metadata"])

    variables = {
        "id": order_id,
        "input": {
            "metadata": [{"key": key_1, "value": new_value}],
            "privateMetadata": [{"key": key_2, "value": new_value}],
        },
    }
    # when
    with race_condition.RunBefore(
        "saleor.graphql.order.mutations.order_update.update_meta_fields",
        update_metadata,
    ):
        response = staff_api_client.post_graphql(ORDER_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orderUpdate"]["order"]
    assert order_data
    assert not content["data"]["orderUpdate"]["errors"]
    order.refresh_from_db()
    resolve_metadata = {item["key"]: item["value"] for item in order_data["metadata"]}
    assert (
        resolve_metadata
        == {key_1: new_value, key_2: value_changed_in_meantime}
        == order.metadata
    )
    resolve_private_metadata = {
        item["key"]: item["value"] for item in order_data["privateMetadata"]
    }
    assert (
        resolve_private_metadata
        == {
            key_2: new_value,
            key_1: value_changed_in_meantime,
        }
        == order.private_metadata
    )
