from unittest import mock

from ....account.notifications import get_default_user_payload
from ....csv import ExportEvents
from ....csv.models import ExportEvent
from ....csv.notifications import get_default_export_payload
from ....order.notifications import get_default_order_payload
from ...email_common import EmailConfig
from ..tasks import (
    send_email_with_link_to_download_file_task,
    send_export_failed_email_task,
    send_set_staff_password_email_task,
    send_staff_order_confirmation_email_task,
    send_staff_password_reset_email_task,
)


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_staff_password_reset_email_task_default_template(
    mocked_send_mail, email_dict_config, customer_user
):
    token = "token123"
    recipient_email = "admin@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }

    send_staff_password_reset_email_task(
        recipient_email,
        payload,
        email_dict_config,
        "subject",
        "template",
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.admin_email.tasks.send_email")
def test_send_staff_password_reset_email_task_custom_template(
    mocked_send_email, email_dict_config, admin_email_plugin, customer_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    admin_email_plugin(
        staff_password_reset_template=expected_template_str,
        staff_password_reset_subject=expected_subject,
    )
    token = "token123"
    recipient_email = "admin@example.com"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "reset_url": f"http://localhost:8000/redirect{token}",
        "domain": "localhost:8000",
        "site_name": "Saleor",
    }

    send_staff_password_reset_email_task(
        recipient_email,
        payload,
        email_dict_config,
        expected_subject,
        expected_template_str,
    )

    email_config = EmailConfig(**email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_set_staff_password_email_task_default_template(
    mocked_send_mail, email_dict_config, customer_user
):
    recipient_email = "user@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "password_set_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_set_staff_password_email_task(
        recipient_email,
        payload,
        email_dict_config,
        "subject",
        "template",
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called


@mock.patch("saleor.plugins.admin_email.tasks.send_email")
def test_send_set_staff_password_email_task_custom_template(
    mocked_send_email, email_dict_config, admin_email_plugin, customer_user
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    admin_email_plugin(
        set_staff_password_template=expected_template_str,
        set_staff_password_title=expected_subject,
    )
    recipient_email = "user@example.com"
    token = "token123"
    payload = {
        "user": get_default_user_payload(customer_user),
        "recipient_email": recipient_email,
        "token": token,
        "password_set_url": f"http://localhost:8000/redirect{token}",
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_set_staff_password_email_task(
        recipient_email,
        payload,
        email_dict_config,
        expected_subject,
        expected_template_str,
    )

    email_config = EmailConfig(**email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_email_with_link_to_download_file_task_default_template(
    mocked_send_mail, email_dict_config, customer_user, user_export_file
):
    recipient_email = "admin@example.com"
    csv_url = "http://127.0.0.1:8000"

    payload = {
        "export": get_default_export_payload(user_export_file),
        "csv_link": csv_url,
        "recipient_email": user_export_file.user.email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }
    send_email_with_link_to_download_file_task(
        recipient_email,
        payload,
        email_dict_config,
        "subject",
        "template",
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called
    assert ExportEvent.objects.filter(
        export_file=user_export_file,
        user=user_export_file.user,
        type=ExportEvents.EXPORTED_FILE_SENT,
    ).exists()


@mock.patch("saleor.plugins.admin_email.tasks.send_email")
def test_send_email_with_link_to_download_file_task_custom_template(
    mocked_send_email, email_dict_config, admin_email_plugin, user_export_file
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    admin_email_plugin(
        csv_product_export=expected_template_str,
        csv_product_export_title=expected_subject,
    )
    recipient_email = "admin@example.com"
    csv_url = "http://127.0.0.1:8000"

    payload = {
        "export": get_default_export_payload(user_export_file),
        "csv_link": csv_url,
        "recipient_email": user_export_file.user.email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_email_with_link_to_download_file_task(
        recipient_email,
        payload,
        email_dict_config,
        expected_subject,
        expected_template_str,
    )

    email_config = EmailConfig(**email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )
    assert ExportEvent.objects.filter(
        export_file=user_export_file,
        user=user_export_file.user,
        type=ExportEvents.EXPORTED_FILE_SENT,
    ).exists()


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_export_failed_email_task_default_template(
    mocked_send_mail, email_dict_config, user_export_file
):
    recipient_email = "admin@example.com"
    payload = {
        "export": get_default_export_payload(user_export_file),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_export_failed_email_task(
        recipient_email,
        payload,
        email_dict_config,
        "subject",
        "template",
    )

    # confirm that mail has correct structure and email was sent
    assert mocked_send_mail.called
    assert ExportEvent.objects.filter(
        export_file=user_export_file,
        user=user_export_file.user,
        type=ExportEvents.EXPORT_FAILED_INFO_SENT,
    )


@mock.patch("saleor.plugins.admin_email.tasks.send_email")
def test_send_export_failed_email_task_custom_template(
    mocked_send_email, email_dict_config, admin_email_plugin, user_export_file
):
    expected_template_str = "<html><body>Template body</body></html>"
    expected_subject = "Test Email Subject"
    admin_email_plugin(
        csv_product_export_failed=expected_template_str,
        csv_product_export_failed_title=expected_subject,
    )
    recipient_email = "admin@example.com"
    payload = {
        "export": get_default_export_payload(user_export_file),
        "recipient_email": recipient_email,
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_export_failed_email_task(
        recipient_email,
        payload,
        email_dict_config,
        expected_subject,
        expected_template_str,
    )

    email_config = EmailConfig(**email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )
    assert ExportEvent.objects.filter(
        export_file=user_export_file,
        user=user_export_file.user,
        type=ExportEvents.EXPORT_FAILED_INFO_SENT,
    )


@mock.patch("saleor.plugins.email_common.send_mail")
def test_send_staff_order_confirmation_email_task_default_template(
    mocked_send_mail, email_dict_config, order_with_lines
):
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(
            order_with_lines, "http://localhost:8000/redirect"
        ),
        "recipient_list": [recipient_email],
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_staff_order_confirmation_email_task(
        [recipient_email],
        payload,
        email_dict_config,
        "subject",
        "template",
    )

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
    recipient_email = "user@example.com"
    payload = {
        "order": get_default_order_payload(
            order_with_lines, "http://localhost:8000/redirect"
        ),
        "recipient_list": [recipient_email],
        "site_name": "Saleor",
        "domain": "localhost:8000",
    }

    send_staff_order_confirmation_email_task(
        [recipient_email],
        payload,
        email_dict_config,
        expected_subject,
        expected_template_str,
    )

    email_config = EmailConfig(**email_dict_config)
    mocked_send_email.assert_called_with(
        config=email_config,
        recipient_list=[recipient_email],
        context=payload,
        subject=expected_subject,
        template_str=expected_template_str,
    )
