import json
from unittest.mock import patch

import pytest
from graphql_relay.node.node import to_global_id

from ....account.models import User
from ....core.notify_events import UserNotifyEvent
from ....graphql.tests.utils import assert_no_permission
from ....product.models import ProductVariant

query_test_data = [
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
            },
            "pluginId": "",
        },
        200,
    ),
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
            },
            "pluginId": "WRONG-TEST-PLUGIN",
        },
        200,
    ),
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
                "externalEventType": {},
            }
        },
        200,
    ),
    (
        {"input": {"extraPayload": json.dumps("{}"), "externalEventType": {}}},
        400,
    ),
    ({"input": {"ids": [], "externalEventType": {}}}, 200),
    (
        {
            "input": {
                "ids": [],
                "extraPayload": json.dumps("{}"),
            }
        },
        400,
    ),
]


@pytest.mark.parametrize("variables, status_code", query_test_data)
def test_query(
    variables,
    status_code,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_users,
):
    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
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
    permission_manage_products,
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
            "extraPayload": "{}",
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        }
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_products],
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
            "extraPayload": "{}",
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
    permission_manage_products,
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
            "extraPayload": json.dumps(test_json),
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
        "pluginId": plugin.PLUGIN_ID,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_products],
    )

    assert response.status_code == 200
    payload = sendgrid_plugin_notify.call_args[1]["payload"]["extra_payload"]
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
    permission_manage_users,
):

    test_json = {"TEST": "VALUE", "TEST_LIST": ["GUEST1", "GUEST2"]}
    plugin = sendgrid_email_plugin(
        active=True, api_key="AB12", account_password_reset_template_id="123"
    )
    variables = {
        "input": {
            "ids": [to_global_id(User.__name__, user.id) for user in staff_users],
            "extraPayload": json.dumps(test_json),
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
        "pluginId": plugin.PLUGIN_ID,
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_users],
    )

    assert response.status_code == 200
    payload = sendgrid_plugin_notify.call_args[1]["payload"]["extra_payload"]
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
        permission_manage_orders,
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
            permission_manage_orders,
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
        permission_manage_products,
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
            permission_manage_products,
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
        permission_manage_products,
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
            permission_manage_products,
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
        permission_manage_users,
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
            permission_manage_users,
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
                "extraPayload": "{}",
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
