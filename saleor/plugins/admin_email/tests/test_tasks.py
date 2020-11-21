from unittest import mock
from urllib.parse import urlencode

from ....core.notifications import get_site_context
from ....core.utils.url import prepare_url
from ....order.notifications import get_default_order_payload
from ...email_common import EmailConfig
from ..tasks import (
    send_email_with_link_to_download_file_task,
    send_export_failed_email_task,
    send_set_staff_password_email_task,
    send_staff_order_confirmation_email_task,
)


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_set_staff_password_email_task_default_template(
    mocked_send_mail, email_dict_config
):
    recipient_email = "admin@example.com"
    redirect_url = "http://127.0.0.1:8000"
    token = "token123"

    send_set_staff_password_email_task(
        recipient_email, redirect_url, token, email_dict_config
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.admin_email.tasks.send_email")
def test_send_set_staff_password_email_task_custom_template(
    mocked_send_email, email_dict_config, admin_email_plugin
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    admin_email_plugin(
        set_staff_password_template=expected_template_str,
        set_staff_password_title=expected_subject,
    )
    recipient_email = "admin@example.com"
    redirect_url = "http://127.0.0.1:8000"
    token = "token123"

    params = urlencode({"email": recipient_email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    ctx = get_site_context()
    ctx["password_set_url"] = password_set_url

    send_set_staff_password_email_task(
        recipient_email, redirect_url, token, email_dict_config
    )

    email_config = EmailConfig(**email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=ctx,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_email_with_link_to_download_file_task_default_template(
    mocked_send_mail, email_dict_config
):
    recipient_email = "admin@example.com"
    csv_url = "http://127.0.0.1:8000"

    send_email_with_link_to_download_file_task(
        recipient_email, csv_url, email_dict_config
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.admin_email.tasks.send_email")
def test_send_email_with_link_to_download_file_task_custom_template(
    mocked_send_email, email_dict_config, admin_email_plugin
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    admin_email_plugin(
        csv_product_export=expected_template_str,
        csv_product_export_title=expected_subject,
    )
    recipient_email = "admin@example.com"
    csv_url = "http://127.0.0.1:8000"

    ctx = get_site_context()
    ctx["csv_link"] = csv_url

    send_email_with_link_to_download_file_task(
        recipient_email, csv_url, email_dict_config
    )

    email_config = EmailConfig(**email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=ctx,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_export_failed_email_task_default_template(
    mocked_send_mail, email_dict_config
):
    recipient_email = "admin@example.com"

    send_export_failed_email_task(recipient_email, email_dict_config)

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.admin_email.tasks.send_email")
def test_send_export_failed_email_task_custom_template(
    mocked_send_email, email_dict_config, admin_email_plugin
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    admin_email_plugin(
        csv_product_export_failed=expected_template_str,
        csv_product_export_failed_title=expected_subject,
    )
    recipient_email = "admin@example.com"

    ctx = get_site_context()

    send_export_failed_email_task(recipient_email, email_dict_config)

    email_config = EmailConfig(**email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=ctx,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_staff_order_confirmation_email_task_default_template(
    mocked_send_mail, email_dict_config, order_with_lines
):
    payload = {
        "order": get_default_order_payload(order_with_lines),
        "recipient_list": ["admin@example.com"],
    }

    send_staff_order_confirmation_email_task(payload, email_dict_config)

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.admin_email.tasks.send_email")
def test_send_staff_order_confirmation_email_task_custom_template(
    mocked_send_email, order_with_lines, email_dict_config, admin_email_plugin
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    admin_email_plugin(
        staff_order_confirmation=expected_template_str,
        staff_order_confirmation_title=expected_subject,
    )
    recipient_email = "admin@example.com"

    payload = {
        "order": get_default_order_payload(order_with_lines),
        "recipient_list": ["admin@example.com"],
    }

    ctx = get_site_context()
    payload.update(ctx)

    send_staff_order_confirmation_email_task(payload, email_dict_config)

    email_config = EmailConfig(**email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )
