from unittest import mock

from django.core.files import File
from templated_email import get_connection

from saleor.csv import ExportEvents, emails
from saleor.csv.models import ExportEvent


@mock.patch("saleor.csv.emails.send_templated_mail")
def test_send_email_with_link_to_download_file(
    mocked_templated_email, site_settings, user_export_file, tmpdir, media_root
):
    # given
    file_mock = mock.MagicMock(spec=File)
    file_mock.name = "temp_file.csv"

    user_export_file.content_file = file_mock
    user_export_file.save()

    # when
    emails.send_email_with_link_to_download_file(
        user_export_file, "export_products_success"
    )

    # then
    template = emails.EXPORT_TEMPLATES["export_products_success"]
    ctx = {
        "csv_link": f"http://mirumee.com/media/export_files/{file_mock.name}",
        "domain": "mirumee.com",
        "site_name": "mirumee.com",
    }
    recipients = [user_export_file.user.email]
    expected_call_kwargs = {
        "context": ctx,
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)

    assert ExportEvent.objects.filter(
        export_file=user_export_file,
        user=user_export_file.user,
        type=ExportEvents.EXPORTED_FILE_SENT,
    ).exists()


@mock.patch("saleor.csv.emails.send_templated_mail")
def test_send_email_with_link_to_download_file_for_app(
    mocked_templated_email, app_export_file, app
):
    # when
    emails.send_email_with_link_to_download_file(
        app_export_file, "export_products_success"
    )

    # then
    mocked_templated_email.assert_not_called()

    assert not ExportEvent.objects.filter(
        export_file=app_export_file,
        user=app_export_file.user,
        type=ExportEvents.EXPORTED_FILE_SENT,
    ).exists()


@mock.patch("saleor.csv.emails.send_templated_mail")
def test_send_export_failed_info(
    mocked_templated_email, site_settings, user_export_file, tmpdir, media_root
):
    file_mock = mock.MagicMock(spec=File)
    file_mock.name = "temp_file.csv"

    user_export_file.content_file = file_mock
    user_export_file.save()

    emails.send_export_failed_info(user_export_file, "export_failed")
    template = emails.EXPORT_TEMPLATES["export_failed"]
    ctx = {
        "domain": "mirumee.com",
        "site_name": "mirumee.com",
    }
    recipients = [user_export_file.user.email]
    expected_call_kwargs = {
        "context": ctx,
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)

    assert ExportEvent.objects.filter(
        export_file=user_export_file,
        user=user_export_file.user,
        type=ExportEvents.EXPORT_FAILED_INFO_SENT,
    )


@mock.patch("saleor.csv.emails.send_templated_mail")
def test_send_export_failed_info_for_app(mocked_templated_email, app_export_file, app):
    # when
    emails.send_export_failed_info(app_export_file, "export_failed")

    # then
    mocked_templated_email.assert_not_called()

    assert not ExportEvent.objects.filter(
        export_file=app_export_file,
        user=app_export_file.user,
        type=ExportEvents.EXPORTED_FILE_SENT,
    ).exists()
