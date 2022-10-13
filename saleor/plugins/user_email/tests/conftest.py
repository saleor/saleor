from unittest.mock import patch

import pytest

from ....plugins.models import EmailTemplate, PluginConfiguration
from ...email_common import DEFAULT_EMAIL_VALUE
from ...manager import get_plugins_manager
from ..constants import (
    ACCOUNT_CHANGE_EMAIL_CONFIRM_DEFAULT_SUBJECT,
    ACCOUNT_CHANGE_EMAIL_CONFIRM_SUBJECT_FIELD,
    ACCOUNT_CHANGE_EMAIL_CONFIRM_TEMPLATE_FIELD,
    ACCOUNT_CHANGE_EMAIL_REQUEST_DEFAULT_SUBJECT,
    ACCOUNT_CHANGE_EMAIL_REQUEST_SUBJECT_FIELD,
    ACCOUNT_CHANGE_EMAIL_REQUEST_TEMPLATE_FIELD,
    ACCOUNT_CONFIRMATION_DEFAULT_SUBJECT,
    ACCOUNT_CONFIRMATION_SUBJECT_FIELD,
    ACCOUNT_CONFIRMATION_TEMPLATE_FIELD,
    ACCOUNT_DELETE_DEFAULT_SUBJECT,
    ACCOUNT_DELETE_SUBJECT_FIELD,
    ACCOUNT_DELETE_TEMPLATE_FIELD,
    ACCOUNT_PASSWORD_RESET_DEFAULT_SUBJECT,
    ACCOUNT_PASSWORD_RESET_SUBJECT_FIELD,
    ACCOUNT_PASSWORD_RESET_TEMPLATE_FIELD,
    ACCOUNT_SET_CUSTOMER_PASSWORD_DEFAULT_SUBJECT,
    ACCOUNT_SET_CUSTOMER_PASSWORD_SUBJECT_FIELD,
    ACCOUNT_SET_CUSTOMER_PASSWORD_TEMPLATE_FIELD,
    INVOICE_READY_DEFAULT_SUBJECT,
    INVOICE_READY_SUBJECT_FIELD,
    INVOICE_READY_TEMPLATE_FIELD,
    ORDER_CANCELED_DEFAULT_SUBJECT,
    ORDER_CANCELED_SUBJECT_FIELD,
    ORDER_CANCELED_TEMPLATE_FIELD,
    ORDER_CONFIRMATION_DEFAULT_SUBJECT,
    ORDER_CONFIRMATION_SUBJECT_FIELD,
    ORDER_CONFIRMATION_TEMPLATE_FIELD,
    ORDER_CONFIRMED_DEFAULT_SUBJECT,
    ORDER_CONFIRMED_SUBJECT_FIELD,
    ORDER_CONFIRMED_TEMPLATE_FIELD,
    ORDER_FULFILLMENT_CONFIRMATION_DEFAULT_SUBJECT,
    ORDER_FULFILLMENT_CONFIRMATION_SUBJECT_FIELD,
    ORDER_FULFILLMENT_CONFIRMATION_TEMPLATE_FIELD,
    ORDER_FULFILLMENT_UPDATE_DEFAULT_SUBJECT,
    ORDER_FULFILLMENT_UPDATE_SUBJECT_FIELD,
    ORDER_FULFILLMENT_UPDATE_TEMPLATE_FIELD,
    ORDER_PAYMENT_CONFIRMATION_DEFAULT_SUBJECT,
    ORDER_PAYMENT_CONFIRMATION_SUBJECT_FIELD,
    ORDER_PAYMENT_CONFIRMATION_TEMPLATE_FIELD,
    ORDER_REFUND_CONFIRMATION_DEFAULT_SUBJECT,
    ORDER_REFUND_CONFIRMATION_SUBJECT_FIELD,
    ORDER_REFUND_CONFIRMATION_TEMPLATE_FIELD,
)
from ..plugin import UserEmailPlugin


@pytest.fixture
def user_email_dict_config():
    return {
        "host": "localhost",
        "port": "1025",
        "username": None,
        "password": None,
        "use_ssl": False,
        "use_tls": False,
    }


@pytest.fixture
def user_email_plugin(settings, channel_USD):
    def fun(
        host="localhost",
        port="1025",
        username=None,
        password=None,
        sender_name="Admin Name",
        sender_address="admin@example.com",
        use_tls=False,
        use_ssl=False,
        active=True,
        account_confirmation_template=DEFAULT_EMAIL_VALUE,
        account_confirmation_subject=ACCOUNT_CONFIRMATION_DEFAULT_SUBJECT,
        password_reset_template=DEFAULT_EMAIL_VALUE,
        password_reset_subject=ACCOUNT_PASSWORD_RESET_DEFAULT_SUBJECT,
        email_change_request_template=DEFAULT_EMAIL_VALUE,
        email_change_request_subject=ACCOUNT_CHANGE_EMAIL_REQUEST_DEFAULT_SUBJECT,
        email_change_confirm_template=DEFAULT_EMAIL_VALUE,
        email_change_confirm_subject=ACCOUNT_CHANGE_EMAIL_CONFIRM_DEFAULT_SUBJECT,
        account_delete_template=DEFAULT_EMAIL_VALUE,
        account_delete_subject=ACCOUNT_DELETE_DEFAULT_SUBJECT,
        account_set_password_template=DEFAULT_EMAIL_VALUE,
        account_set_password_subject=ACCOUNT_SET_CUSTOMER_PASSWORD_DEFAULT_SUBJECT,
        invoice_ready_template=DEFAULT_EMAIL_VALUE,
        invoice_ready_subject=INVOICE_READY_DEFAULT_SUBJECT,
        order_confirmation_template=DEFAULT_EMAIL_VALUE,
        order_confirmation_subject=ORDER_CONFIRMATION_DEFAULT_SUBJECT,
        order_confirmed_template=DEFAULT_EMAIL_VALUE,
        order_confirmed_subject=ORDER_CONFIRMED_DEFAULT_SUBJECT,
        fulfillment_confirmation_template=DEFAULT_EMAIL_VALUE,
        fulfillment_confirmation_subject=ORDER_FULFILLMENT_CONFIRMATION_DEFAULT_SUBJECT,
        fulfillment_update_template=DEFAULT_EMAIL_VALUE,
        fulfillment_update_subject=ORDER_FULFILLMENT_UPDATE_DEFAULT_SUBJECT,
        payment_confirmation_template=DEFAULT_EMAIL_VALUE,
        payment_confirmation_subject=ORDER_PAYMENT_CONFIRMATION_DEFAULT_SUBJECT,
        order_cancel_template=DEFAULT_EMAIL_VALUE,
        order_cancel_subject=ORDER_CANCELED_DEFAULT_SUBJECT,
        order_refund_template=DEFAULT_EMAIL_VALUE,
        order_refund_subject=ORDER_REFUND_CONFIRMATION_DEFAULT_SUBJECT,
    ):

        settings.PLUGINS = ["saleor.plugins.user_email.plugin.UserEmailPlugin"]
        manager = get_plugins_manager()
        with patch(
            "saleor.plugins.user_email.plugin.validate_default_email_configuration"
        ):
            manager.save_plugin_configuration(
                UserEmailPlugin.PLUGIN_ID,
                channel_USD.slug,
                {
                    "active": active,
                    "configuration": [
                        {"name": "host", "value": host},
                        {"name": "port", "value": port},
                        {"name": "username", "value": username},
                        {"name": "password", "value": password},
                        {"name": "sender_name", "value": sender_name},
                        {"name": "sender_address", "value": sender_address},
                        {"name": "use_tls", "value": use_tls},
                        {"name": "use_ssl", "value": use_ssl},
                        {
                            "name": ACCOUNT_CONFIRMATION_TEMPLATE_FIELD,
                            "value": account_confirmation_template,
                        },
                        {
                            "name": ACCOUNT_CONFIRMATION_SUBJECT_FIELD,
                            "value": account_confirmation_subject,
                        },
                        {
                            "name": ACCOUNT_PASSWORD_RESET_TEMPLATE_FIELD,
                            "value": password_reset_template,
                        },
                        {
                            "name": ACCOUNT_PASSWORD_RESET_SUBJECT_FIELD,
                            "value": password_reset_subject,
                        },
                        {
                            "name": ACCOUNT_CHANGE_EMAIL_REQUEST_TEMPLATE_FIELD,
                            "value": email_change_request_template,
                        },
                        {
                            "name": ACCOUNT_CHANGE_EMAIL_REQUEST_SUBJECT_FIELD,
                            "value": email_change_request_subject,
                        },
                        {
                            "name": ACCOUNT_CHANGE_EMAIL_CONFIRM_TEMPLATE_FIELD,
                            "value": email_change_confirm_template,
                        },
                        {
                            "name": ACCOUNT_CHANGE_EMAIL_CONFIRM_SUBJECT_FIELD,
                            "value": email_change_confirm_subject,
                        },
                        {
                            "name": ACCOUNT_DELETE_TEMPLATE_FIELD,
                            "value": account_delete_template,
                        },
                        {
                            "name": ACCOUNT_DELETE_SUBJECT_FIELD,
                            "value": account_delete_subject,
                        },
                        {
                            "name": ACCOUNT_SET_CUSTOMER_PASSWORD_TEMPLATE_FIELD,
                            "value": account_set_password_template,
                        },
                        {
                            "name": ACCOUNT_SET_CUSTOMER_PASSWORD_SUBJECT_FIELD,
                            "value": account_set_password_subject,
                        },
                        {
                            "name": INVOICE_READY_TEMPLATE_FIELD,
                            "value": invoice_ready_template,
                        },
                        {
                            "name": INVOICE_READY_SUBJECT_FIELD,
                            "value": invoice_ready_subject,
                        },
                        {
                            "name": ORDER_CONFIRMATION_TEMPLATE_FIELD,
                            "value": order_confirmation_template,
                        },
                        {
                            "name": ORDER_CONFIRMATION_SUBJECT_FIELD,
                            "value": order_confirmation_subject,
                        },
                        {
                            "name": ORDER_CONFIRMED_TEMPLATE_FIELD,
                            "value": order_confirmed_template,
                        },
                        {
                            "name": ORDER_CONFIRMED_SUBJECT_FIELD,
                            "value": order_confirmed_subject,
                        },
                        {
                            "name": ORDER_FULFILLMENT_CONFIRMATION_TEMPLATE_FIELD,
                            "value": fulfillment_confirmation_template,
                        },
                        {
                            "name": ORDER_FULFILLMENT_CONFIRMATION_SUBJECT_FIELD,
                            "value": fulfillment_confirmation_subject,
                        },
                        {
                            "name": ORDER_FULFILLMENT_UPDATE_TEMPLATE_FIELD,
                            "value": fulfillment_update_template,
                        },
                        {
                            "name": ORDER_FULFILLMENT_UPDATE_SUBJECT_FIELD,
                            "value": fulfillment_update_subject,
                        },
                        {
                            "name": ORDER_PAYMENT_CONFIRMATION_TEMPLATE_FIELD,
                            "value": payment_confirmation_template,
                        },
                        {
                            "name": ORDER_PAYMENT_CONFIRMATION_SUBJECT_FIELD,
                            "value": payment_confirmation_subject,
                        },
                        {
                            "name": ORDER_CANCELED_TEMPLATE_FIELD,
                            "value": order_cancel_template,
                        },
                        {
                            "name": ORDER_CANCELED_SUBJECT_FIELD,
                            "value": order_cancel_subject,
                        },
                        {
                            "name": ORDER_REFUND_CONFIRMATION_TEMPLATE_FIELD,
                            "value": order_refund_template,
                        },
                        {
                            "name": ORDER_REFUND_CONFIRMATION_SUBJECT_FIELD,
                            "value": order_refund_subject,
                        },
                    ],
                },
            )
        manager = get_plugins_manager()
        return manager.plugins_per_channel[channel_USD.slug][0]

    return fun


@pytest.fixture
def user_email_template(user_email_plugin):
    plugin = user_email_plugin()
    config = PluginConfiguration.objects.get(identifier=plugin.PLUGIN_ID)
    return EmailTemplate.objects.create(
        name=ORDER_CONFIRMATION_TEMPLATE_FIELD,
        value="Custom order confirmation template",
        plugin_configuration=config,
    )
