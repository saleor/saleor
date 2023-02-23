import pytest

from ....plugins.sendgrid.plugin import SendgridEmailPlugin
from ...manager import get_plugins_manager


@pytest.fixture
def sendgrid_email_plugin(settings, channel_USD):
    def fun(
        active=True,
        sender_name=None,
        sender_address=None,
        account_confirmation_template_id=None,
        account_set_customer_password_template_id=None,
        account_delete_template_id=None,
        account_change_email_confirm_template_id=None,
        account_change_email_request_template_id=None,
        account_password_reset_template_id=None,
        invoice_ready_template_id=None,
        order_confirmation_template_id=None,
        order_confirmed_template_id=None,
        order_fulfillment_confirmation_template_id=None,
        order_fulfillment_update_template_id=None,
        order_payment_confirmation_template_id=None,
        order_canceled_template_id=None,
        order_refund_confirmation_template_id=None,
        send_gift_card_template_id=None,
        api_key=None,
    ):
        settings.PLUGINS = ["saleor.plugins.sendgrid.plugin.SendgridEmailPlugin"]
        manager = get_plugins_manager()
        manager.save_plugin_configuration(
            SendgridEmailPlugin.PLUGIN_ID,
            channel_USD.slug,
            {
                "active": active,
                "configuration": [
                    {"name": "sender_name", "value": sender_name},
                    {"name": "sender_address", "value": sender_address},
                    {
                        "name": "account_confirmation_template_id",
                        "value": account_confirmation_template_id,
                    },
                    {
                        "name": "account_set_customer_password_template_id",
                        "value": account_set_customer_password_template_id,
                    },
                    {
                        "name": "account_delete_template_id",
                        "value": account_delete_template_id,
                    },
                    {
                        "name": "account_change_email_confirm_template_id",
                        "value": account_change_email_confirm_template_id,
                    },
                    {
                        "name": "account_change_email_request_template_id",
                        "value": account_change_email_request_template_id,
                    },
                    {
                        "name": "account_password_reset_template_id",
                        "value": account_password_reset_template_id,
                    },
                    {
                        "name": "invoice_ready_template_id",
                        "value": invoice_ready_template_id,
                    },
                    {
                        "name": "order_confirmation_template_id",
                        "value": order_confirmation_template_id,
                    },
                    {
                        "name": "order_confirmed_template_id",
                        "value": order_confirmed_template_id,
                    },
                    {
                        "name": "order_fulfillment_confirmation_template_id",
                        "value": order_fulfillment_confirmation_template_id,
                    },
                    {
                        "name": "order_fulfillment_update_template_id",
                        "value": order_fulfillment_update_template_id,
                    },
                    {
                        "name": "order_payment_confirmation_template_id",
                        "value": order_payment_confirmation_template_id,
                    },
                    {
                        "name": "order_canceled_template_id",
                        "value": order_canceled_template_id,
                    },
                    {
                        "name": "order_refund_confirmation_template_id",
                        "value": order_refund_confirmation_template_id,
                    },
                    {
                        "name": "send_gift_card_template_id",
                        "value": send_gift_card_template_id,
                    },
                    {"name": "api_key", "value": api_key},
                ],
            },
        )
        manager = get_plugins_manager()
        return manager.plugins_per_channel[channel_USD.slug][0]

    return fun
