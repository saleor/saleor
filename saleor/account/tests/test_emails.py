from unittest import mock

from django.core import mail
from templated_email import get_connection

from ...plugins.manager import get_plugins_manager
from .. import notifications


@mock.patch("saleor.plugins.user_email.tasks.send_templated_mail")
def test_send_email_request_change(
    mocked_templated_email, site_settings, customer_user, user_email_plugin
):
    user_email_plugin()
    new_email = "example@example.com"
    template = notifications.REQUEST_EMAIL_CHANGE_TEMPLATE
    redirect_url = "localhost"
    token = "token_example"

    manager = get_plugins_manager()
    notifications.send_request_user_change_email_notification(
        redirect_url, customer_user, new_email, token, manager
    )
    ctx = {
        "domain": "mirumee.com",
        "redirect_url": "localhost?token=token_example",
        "site_name": "mirumee.com",
    }
    recipients = [new_email]

    expected_call_kwargs = {
        "context": ctx,
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    # mocked_templated_email.assert_called_once()
    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.plugins.user_email.tasks.send_templated_mail")
def test_send_email_changed_notification(
    mocked_templated_email, site_settings, customer_user, user_email_plugin
):
    user_email_plugin()
    old_email = "example@example.com"
    template = notifications.EMAIL_CHANGED_NOTIFICATION_TEMPLATE
    notifications.send_user_change_email_notification(
        old_email, customer_user, get_plugins_manager()
    )
    ctx = {
        "domain": "mirumee.com",
        "site_name": "mirumee.com",
    }
    recipients = [old_email]

    expected_call_kwargs = {
        "context": ctx,
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    # mocked_templated_email.assert_called_once()
    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)
