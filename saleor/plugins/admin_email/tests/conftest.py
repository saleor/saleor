from unittest.mock import patch

import pytest

from ....plugins.models import EmailTemplate, PluginConfiguration
from ...email_common import DEFAULT_EMAIL_VALUE
from ...manager import get_plugins_manager
from ..constants import (
    CSV_EXPORT_FAILED_DEFAULT_SUBJECT,
    CSV_EXPORT_FAILED_SUBJECT_FIELD,
    CSV_EXPORT_FAILED_TEMPLATE_FIELD,
    CSV_EXPORT_SUCCESS_DEFAULT_SUBJECT,
    CSV_EXPORT_SUCCESS_SUBJECT_FIELD,
    CSV_EXPORT_SUCCESS_TEMPLATE_FIELD,
    SET_STAFF_PASSWORD_DEFAULT_SUBJECT,
    SET_STAFF_PASSWORD_SUBJECT_FIELD,
    SET_STAFF_PASSWORD_TEMPLATE_FIELD,
    STAFF_ORDER_CONFIRMATION_DEFAULT_SUBJECT,
    STAFF_ORDER_CONFIRMATION_SUBJECT_FIELD,
    STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
    STAFF_PASSWORD_RESET_DEFAULT_SUBJECT,
    STAFF_PASSWORD_RESET_SUBJECT_FIELD,
    STAFF_PASSWORD_RESET_TEMPLATE_FIELD,
)
from ..plugin import AdminEmailPlugin


@pytest.fixture
def email_dict_config():
    return {
        "host": "localhost",
        "port": "1025",
        "username": None,
        "password": None,
        "use_ssl": False,
        "use_tls": False,
    }


@pytest.fixture
def admin_email_plugin(settings):
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
        set_staff_password_template=DEFAULT_EMAIL_VALUE,
        staff_order_confirmation=DEFAULT_EMAIL_VALUE,
        csv_product_export=DEFAULT_EMAIL_VALUE,
        csv_product_export_failed=DEFAULT_EMAIL_VALUE,
        set_staff_password_title=STAFF_ORDER_CONFIRMATION_DEFAULT_SUBJECT,
        staff_order_confirmation_title=SET_STAFF_PASSWORD_DEFAULT_SUBJECT,
        csv_product_export_title=CSV_EXPORT_SUCCESS_DEFAULT_SUBJECT,
        csv_product_export_failed_title=CSV_EXPORT_FAILED_DEFAULT_SUBJECT,
        staff_password_reset_template=DEFAULT_EMAIL_VALUE,
        staff_password_reset_subject=STAFF_PASSWORD_RESET_DEFAULT_SUBJECT,
    ):
        settings.PLUGINS = ["saleor.plugins.admin_email.plugin.AdminEmailPlugin"]
        manager = get_plugins_manager(allow_replica=False)
        with patch(
            "saleor.plugins.admin_email.plugin.validate_default_email_configuration"
        ):
            manager.save_plugin_configuration(
                AdminEmailPlugin.PLUGIN_ID,
                None,
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
                            "name": STAFF_PASSWORD_RESET_TEMPLATE_FIELD,
                            "value": staff_password_reset_template,
                        },
                        {
                            "name": SET_STAFF_PASSWORD_TEMPLATE_FIELD,
                            "value": set_staff_password_template,
                        },
                        {
                            "name": STAFF_ORDER_CONFIRMATION_TEMPLATE_FIELD,
                            "value": staff_order_confirmation,
                        },
                        {
                            "name": CSV_EXPORT_SUCCESS_TEMPLATE_FIELD,
                            "value": csv_product_export,
                        },
                        {
                            "name": CSV_EXPORT_FAILED_TEMPLATE_FIELD,
                            "value": csv_product_export_failed,
                        },
                        {
                            "name": STAFF_PASSWORD_RESET_SUBJECT_FIELD,
                            "value": staff_password_reset_subject,
                        },
                        {
                            "name": STAFF_ORDER_CONFIRMATION_SUBJECT_FIELD,
                            "value": staff_order_confirmation_title,
                        },
                        {
                            "name": SET_STAFF_PASSWORD_SUBJECT_FIELD,
                            "value": set_staff_password_title,
                        },
                        {
                            "name": CSV_EXPORT_SUCCESS_SUBJECT_FIELD,
                            "value": csv_product_export_title,
                        },
                        {
                            "name": CSV_EXPORT_FAILED_SUBJECT_FIELD,
                            "value": csv_product_export_failed_title,
                        },
                    ],
                },
            )
        manager = get_plugins_manager(allow_replica=False)
        manager.get_all_plugins()
        return manager.global_plugins[0]

    return fun


@pytest.fixture
def admin_email_template(admin_email_plugin):
    plugin = admin_email_plugin()
    config = PluginConfiguration.objects.get(identifier=plugin.PLUGIN_ID)
    return EmailTemplate.objects.create(
        name=STAFF_PASSWORD_RESET_TEMPLATE_FIELD,
        value="Custom staff reset password email template",
        plugin_configuration=config,
    )
