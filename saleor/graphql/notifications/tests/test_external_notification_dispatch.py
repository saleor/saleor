import json
from unittest.mock import patch

from graphql_relay.node.node import to_global_id

from ....core.notify_events import UserNotifyEvent
from ....product.models import ProductVariant
from ....webhook.payloads import generate_product_variant_payload


@patch("saleor.plugins.manager.PluginsManager.notify_in_single_plugin")
def test_notify_sendgrid_via_external_notification_trigger_for_sendgrid_plugin(
    notify_single_plugin_mock,
    settings,
    product_with_single_variant,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_products,
    sendgrid_email_plugin,
):

    settings.PLUGINS = [
        "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
    ]
    sendgrid_email_plugin(active=True, api_key="AB12")
    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    variables = {
        "input": {
            "ids": [
                to_global_id(ProductVariant.__name__, pk)
                for pk in product_with_single_variant.variants.values_list(
                    "pk", flat=True
                )
            ],
            "extraPayload": '{"recipient_email":"test@gmail.com"}',
            "externalEventType": test_template_id,
        },
        "pluginId": "mirumee.notifications.sendgrid_email",
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_products],
    )

    assert response.status_code == 200
    notify_single_plugin_mock.assert_called_once()


@patch("saleor.plugins.webhook.plugin.WebhookPlugin.notify")
def test_external_notification_trigger_for_all_plugins_args_checking(
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

    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    variables = {
        "input": {
            "ids": [
                to_global_id(ProductVariant.__name__, pk)
                for pk in product_with_single_variant.variants.values_list(
                    "pk", flat=True
                )
            ],
            "extraPayload": '{"recipient_email":"test@gmail.com"}',
            "externalEventType": test_template_id,
        },
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_products],
    )
    expected_payload = json.loads(
        generate_product_variant_payload(product_with_single_variant.variants.all())
    )
    for payload in expected_payload:
        payload["extra_payload"] = {"recipient_email": "test@gmail.com"}

    assert response.status_code == 200
    webhook_plugin_notify.assert_called_once_with(
        test_template_id, expected_payload[0], previous_value=None
    )


def test_notification_trigger_for_all_plugins_logs_checking(
    settings,
    product_with_single_variant,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_products,
    caplog,
):

    settings.PLUGINS = [
        "saleor.plugins.user_email.plugin.UserEmailPlugin",
        "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
        "saleor.plugins.webhook.plugin.WebhookPlugin",
        "saleor.plugins.admin_email.plugin.AdminEmailPlugin",
    ]

    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    variables = {
        "input": {
            "ids": [
                to_global_id(ProductVariant.__name__, pk)
                for pk in product_with_single_variant.variants.values_list(
                    "pk", flat=True
                )
            ],
            "extraPayload": '{"recipient_email":"test@gmail.com"}',
            "externalEventType": test_template_id,
        },
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_products],
    )

    assert response.status_code == 200
    assert (
        f"Webhook notify_user triggered for {test_template_id} notify event."
        in caplog.text
    )


def test_notify_sendgrid_via_external_notification_trigger_for_all_plugins_lack_of_logs(
    settings,
    product_with_single_variant,
    external_notification_trigger_query,
    staff_api_client,
    permission_manage_products,
    caplog,
):

    settings.PLUGINS = [
        "saleor.plugins.user_email.plugin.UserEmailPlugin",
        "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
        "saleor.plugins.webhook.plugin.WebhookPlugin",
        "saleor.plugins.admin_email.plugin.AdminEmailPlugin",
    ]

    test_template_id = "2efac70d-64ed-4e57-9951-f87e14d7e60e"

    variables = {
        "input": {
            "ids": [
                to_global_id(ProductVariant.__name__, pk)
                for pk in product_with_single_variant.variants.values_list(
                    "pk", flat=True
                )
            ],
            "extraPayload": '{"recipient_email":"test@gmail.com"}',
            "externalEventType": UserNotifyEvent.ORDER_CANCELED,
        },
    }

    response = staff_api_client.post_graphql(
        external_notification_trigger_query,
        variables,
        permissions=[permission_manage_products],
    )

    assert response.status_code == 200
    assert (
        f"Webhook notify_user triggered for {test_template_id} notify event."
        not in caplog.text
    )
    assert (
        f"Send email with event {test_template_id} as dynamic template ID."
        not in caplog.text
    )
