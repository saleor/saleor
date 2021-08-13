import json
from unittest.mock import patch

import pytest
from graphql_relay.node.node import to_global_id

from ....account.models import User
from ....core.notify_events import UserNotifyEvent
from ....graphql.tests.utils import assert_no_permission
from ....product.models import ProductVariant
from .conftest import query_test_data


@pytest.mark.parametrize("variables, status_code", query_test_data)
def test_query(
    variables,
    status_code,
    external_notification_trigger_query,
    staff_api_client,
    manage_users_permission,
):
    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[manage_users_permission],
        check_no_permissions=False,
    )
    assert response.status_code == status_code


@patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
@patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
@patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
@patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
def test_notify_sendgrid_via_external_notification_trigger_for_all_plugins(
    sendgrid_plugin_notify,
    user_email_plugin_notify,
    admin_email_plugin_notify,
    webhook_plugin_notify,
    settings,
    product_with_single_variant,
    external_notification_trigger_query,
    staff_api_client,
    product_permission,
):

    settings.PLUGINS = [
        "saleor.plugins.user_email.plugin.UserEmailPlugin",
        "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
        "saleor.plugins.webhook.plugin.WebhookPlugin",
        "saleor.plugins.admin_email.plugin.AdminEmailPlugin",
    ]

    variables = {
        "input": {
            "ids": [
                to_global_id(ProductVariant.__name__, pk)
                for pk in product_with_single_variant.variants.values_list(
                    "pk", flat=True
                )
            ],
            "extraPayloads": "{}",
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        }
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query, variables, permissions=[product_permission]
    )

    assert response.status_code == 200
    sendgrid_plugin_notify.assert_called_once()
    user_email_plugin_notify.assert_called_once()
    admin_email_plugin_notify.assert_called_once()
    webhook_plugin_notify.assert_called_once()


@patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
@patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
@patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
@patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
def test_notify_via_external_notification_trigger_without_permission(
    sendgrid_plugin_notify,
    user_email_plugin_notify,
    admin_email_plugin_notify,
    webhook_plugin_notify,
    product_with_single_variant,
    sendgrid_email_plugin,
    external_notification_trigger_query,
    staff_api_client,
):
    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id="123"
    )
    variables = {
        "input": {
            "ids": [
                to_global_id(ProductVariant.__name__, pk)
                for pk in product_with_single_variant.variants.values_list(
                    "pk", flat=True
                )
            ],
            "extraPayloads": "{}",
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
        "pluginId": plugin.PLUGIN_ID,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query, variables
    )
    assert_no_permission(response)
    assert response.status_code == 200
    sendgrid_plugin_notify.assert_not_called()
    user_email_plugin_notify.assert_not_called()
    admin_email_plugin_notify.assert_not_called()
    webhook_plugin_notify.assert_not_called()


@patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
def test_notify_via_external_notification_trigger_with_extra_payload(
    sendgrid_plugin_notify,
    product_with_single_variant,
    sendgrid_email_plugin,
    external_notification_trigger_query,
    staff_api_client,
    product_permission,
):

    test_json = {"TEST": "VALUE", "TEST_LIST": ["GUEST1", "GUEST2"]}
    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id="123"
    )
    variables = {
        "input": {
            "ids": [
                to_global_id(ProductVariant.__name__, pk)
                for pk in product_with_single_variant.variants.values_list(
                    "pk", flat=True
                )
            ],
            "extraPayloads": json.dumps(test_json),
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
        "pluginId": plugin.PLUGIN_ID,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query, variables, permissions=[product_permission]
    )

    assert response.status_code == 200
    payload = sendgrid_plugin_notify.call_args[1]["payload"]
    assert "TEST" in payload.keys()
    assert "TEST_LIST" in payload.keys()
    assert ["GUEST1", "GUEST2"] == payload.get("TEST_LIST")


@patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
def test_notify_via_external_notification_trigger_with_extra_payload_for_customers(
    sendgrid_plugin_notify,
    staff_users,
    sendgrid_email_plugin,
    external_notification_trigger_query,
    staff_api_client,
    manage_users_permission,
):

    test_json = {"TEST": "VALUE", "TEST_LIST": ["GUEST1", "GUEST2"]}
    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id="123"
    )
    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayloads": json.dumps(test_json),
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
        "pluginId": plugin.PLUGIN_ID,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[manage_users_permission],
    )

    assert response.status_code == 200
    payload = sendgrid_plugin_notify.call_args[1]["payload"]
    assert "TEST" in payload.keys()
    assert "TEST_LIST" in payload.keys()
    assert ["GUEST1", "GUEST2"] == payload.get("TEST_LIST")


class TestSetWithVariousDataTypes:
    @patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
    @patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
    @patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
    @patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
    def test_for_order(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        fulfilled_order,
        order_permission,
    ):
        ids = [to_global_id(fulfilled_order.__class__.__name__, fulfilled_order.id)]
        self._common_part(
            sendgrid_plugin_notify,
            user_email_plugin_notify,
            admin_email_plugin_notify,
            webhook_plugin_notify,
            staff_api_client,
            external_notification_trigger_query,
            sendgrid_email_plugin,
            ids,
            order_permission,
        )

    @patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
    @patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
    @patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
    @patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
    def test_for_fulfillment(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        fulfillment,
        order_permission,
    ):
        ids = [to_global_id(fulfillment.__class__.__name__, fulfillment.id)]
        self._common_part(
            sendgrid_plugin_notify,
            user_email_plugin_notify,
            admin_email_plugin_notify,
            webhook_plugin_notify,
            staff_api_client,
            external_notification_trigger_query,
            sendgrid_email_plugin,
            ids,
            order_permission,
        )

    @patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
    @patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
    @patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
    @patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
    def test_for_list_of_checkouts(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        checkouts_list,
        checkout_permission,
    ):
        ids = [
            to_global_id(checkout.__class__.__name__, checkout.token)
            for checkout in checkouts_list
        ]
        self._common_part(
            sendgrid_plugin_notify,
            user_email_plugin_notify,
            admin_email_plugin_notify,
            webhook_plugin_notify,
            staff_api_client,
            external_notification_trigger_query,
            sendgrid_email_plugin,
            ids,
            checkout_permission,
        )

    @patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
    @patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
    @patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
    @patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
    def test_for_checkout(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        checkout_with_item,
        checkout_permission,
    ):
        ids = [
            to_global_id(
                checkout_with_item.__class__.__name__, checkout_with_item.token
            )
        ]
        self._common_part(
            sendgrid_plugin_notify,
            user_email_plugin_notify,
            admin_email_plugin_notify,
            webhook_plugin_notify,
            staff_api_client,
            external_notification_trigger_query,
            sendgrid_email_plugin,
            ids,
            checkout_permission,
        )

    @patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
    @patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
    @patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
    @patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
    def test_for_invoice(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        fulfilled_order,
        order_permission,
    ):
        invoice = fulfilled_order.invoices.last()
        ids = [to_global_id(invoice.__class__.__name__, invoice.id)]
        self._common_part(
            sendgrid_plugin_notify,
            user_email_plugin_notify,
            admin_email_plugin_notify,
            webhook_plugin_notify,
            staff_api_client,
            external_notification_trigger_query,
            sendgrid_email_plugin,
            ids,
            order_permission,
        )

    @patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
    @patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
    @patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
    @patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
    def test_for_product(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        product,
        product_permission,
    ):
        ids = [to_global_id(product.__class__.__name__, product.id)]
        self._common_part(
            sendgrid_plugin_notify,
            user_email_plugin_notify,
            admin_email_plugin_notify,
            webhook_plugin_notify,
            staff_api_client,
            external_notification_trigger_query,
            sendgrid_email_plugin,
            ids,
            product_permission,
        )

    @patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
    @patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
    @patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
    @patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
    def test_for_product_variants(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        product_with_two_variants,
        product_permission,
    ):
        ids = [
            to_global_id(ProductVariant.__name__, pk)
            for pk in product_with_two_variants.variants.values_list("pk", flat=True)
        ]
        self._common_part(
            sendgrid_plugin_notify,
            user_email_plugin_notify,
            admin_email_plugin_notify,
            webhook_plugin_notify,
            staff_api_client,
            external_notification_trigger_query,
            sendgrid_email_plugin,
            ids,
            product_permission,
        )

    @patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
    @patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
    @patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
    @patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
    def test_for_single_product_variant(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        product_with_single_variant,
        product_permission,
    ):
        ids = [
            to_global_id(ProductVariant.__name__, pk)
            for pk in product_with_single_variant.variants.values_list("pk", flat=True)
        ]
        self._common_part(
            sendgrid_plugin_notify,
            user_email_plugin_notify,
            admin_email_plugin_notify,
            webhook_plugin_notify,
            staff_api_client,
            external_notification_trigger_query,
            sendgrid_email_plugin,
            ids,
            product_permission,
        )

    @patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
    @patch("saleor.plugins.admin_email.plugin.AdminEmailPlugin.notify")
    @patch("saleor.plugins.user_email.plugin.UserEmailPlugin.notify")
    @patch("saleor.plugins.sendgrid.plugin.SendgridEmailPlugin.notify")
    def test_for_customers(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        staff_users,
        manage_users_permission,
    ):
        ids = [to_global_id(User.__name__, user.id) for user in staff_users]
        self._common_part(
            sendgrid_plugin_notify,
            user_email_plugin_notify,
            admin_email_plugin_notify,
            webhook_plugin_notify,
            staff_api_client,
            external_notification_trigger_query,
            sendgrid_email_plugin,
            ids,
            manage_users_permission,
        )

    def _common_part(
        self,
        sendgrid_plugin_notify,
        user_email_plugin_notify,
        admin_email_plugin_notify,
        webhook_plugin_notify,
        staff_api_client,
        external_notification_trigger_query,
        sendgrid_email_plugin,
        ids,
        permissions,
    ):
        plugin = sendgrid_email_plugin(
            active=True, api_key="AB12", account_password_reset_template_id="123"
        )

        variables = {
            "input": {
                "ids": ids,
                "extraPayloads": "{}",
                "externalEventType": UserNotifyEvent.ORDER_CANCELED,
            },
            "pluginId": plugin.PLUGIN_ID,
        }

        response = staff_api_client.post_graphql(
            external_notification_trigger_query, variables, permissions=[permissions]
        )

        assert response.status_code == 200
        assert sendgrid_plugin_notify.call_count == len(ids)
        user_email_plugin_notify.assert_not_called()
        admin_email_plugin_notify.assert_not_called()
        webhook_plugin_notify.assert_not_called()
