from unittest import mock

import pytest


@pytest.mark.skip
@mock.patch("saleor.csv.emails.send_templated_mail")
def test_send_email_with_link_to_download_file(
    mocked_templated_email, site_settings, user_export_file, tmpdir, media_root
):
    # given
    file_mock = mock.MagicMock(spec=File)  # noqa: F821
    file_mock.name = "temp_file.csv"

    user_export_file.content_file = file_mock
    user_export_file.save()

    # when
    emails.send_email_with_link_to_download_file(user_export_file)  # noqa: F821

    # then
    template = emails.EXPORT_TEMPLATES["export_products_success"]  # noqa: F821
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
    email_connection = get_connection()  # noqa: F821
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)

    assert ExportEvent.objects.filter(  # noqa: F821
        export_file=user_export_file,
        user=user_export_file.user,
        type=ExportEvents.EXPORTED_FILE_SENT,  # noqa: F821
    ).exists()


@pytest.mark.skip
@mock.patch("saleor.csv.emails.send_templated_mail")
def test_send_export_failed_info(
    mocked_templated_email, site_settings, user_export_file, tmpdir, media_root
):
    # given
    file_mock = mock.MagicMock(spec=File)  # noqa: F821
    file_mock.name = "temp_file.csv"

    user_export_file.content_file = file_mock
    user_export_file.save()
    expected_recipients = [user_export_file.user.email]

    # when
    emails.send_export_failed_info(user_export_file)  # noqa: F821

    # then
    template = emails.EXPORT_TEMPLATES["export_failed"]  # noqa: F821
    ctx = {
        "domain": "mirumee.com",
        "site_name": "mirumee.com",
    }

    expected_call_kwargs = {
        "context": ctx,
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=expected_recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()  # noqa: F821
    email_connection.get_email_message(to=expected_recipients, **expected_call_kwargs)

    assert ExportEvent.objects.filter(  # noqa: F821
        export_file=user_export_file,
        user=user_export_file.user,
        type=ExportEvents.EXPORT_FAILED_INFO_SENT,  # noqa: F821
    )
