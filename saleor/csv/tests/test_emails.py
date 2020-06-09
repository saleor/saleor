from unittest import mock

from django.core.files import File
from templated_email import get_connection

from saleor.csv import ExportEvents, emails
from saleor.csv.models import ExportEvent


@mock.patch("saleor.csv.emails.send_templated_mail")
def test_send_email_with_link_to_download_file(
    mocked_templated_email, site_settings, export_file, tmpdir, media_root
):
    file_mock = mock.MagicMock(spec=File)
    file_mock.name = "temp_file.csv"

    export_file.content_file = file_mock
    export_file.save()

    emails.send_email_with_link_to_download_file(export_file, "export_products_success")
    template = emails.EXPORT_TEMPLATES["export_products_success"]
    ctx = {
        "csv_link": f"http://mirumee.com/media/export_files/{file_mock.name}",
        "domain": "mirumee.com",
        "site_name": "mirumee.com",
    }
    recipients = [export_file.user.email]
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
        export_file=export_file,
        user=export_file.user,
        type=ExportEvents.EXPORTED_FILE_SENT,
    )


@mock.patch("saleor.csv.emails.send_templated_mail")
def test_send_export_failed_info(
    mocked_templated_email, site_settings, export_file, tmpdir, media_root
):
    file_mock = mock.MagicMock(spec=File)
    file_mock.name = "temp_file.csv"

    export_file.content_file = file_mock
    export_file.save()

    emails.send_export_failed_info(export_file, "export_failed")
    template = emails.EXPORT_TEMPLATES["export_failed"]
    ctx = {
        "domain": "mirumee.com",
        "site_name": "mirumee.com",
    }
    recipients = [export_file.user.email]
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
        export_file=export_file,
        user=export_file.user,
        type=ExportEvents.EXPORT_FAILED_INFO_SENT,
    )
