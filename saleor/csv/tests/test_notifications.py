from unittest import mock

from django.core.files import File
from freezegun import freeze_time

from ...core.notification.utils import get_site_context
from ...core.notify_events import AdminNotifyEvent
from ...core.utils import build_absolute_uri
from .. import notifications
from ..notifications import get_default_export_payload


@freeze_time("2018-05-31 12:00:01")
@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_export_download_link_notification(
    mocked_notify, site_settings, user_export_file, tmpdir, media_root
):
    # given
    file_mock = mock.MagicMock(spec=File)
    file_mock.name = "temp_file.csv"
    data_type = "products"

    user_export_file.content_file = file_mock
    user_export_file.save()

    # when
    notifications.send_export_download_link_notification(user_export_file, data_type)

    # then
    expected_payload = {
        "export": get_default_export_payload(user_export_file),
        "csv_link": build_absolute_uri(user_export_file.content_file.url),
        "recipient_email": user_export_file.user.email,
        "data_type": data_type,
        **get_site_context(),
    }

    mocked_notify.assert_called_once_with(
        AdminNotifyEvent.CSV_EXPORT_SUCCESS, expected_payload
    )


@freeze_time("2018-05-31 12:00:01")
@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_send_export_failed_info(
    mocked_notify, site_settings, user_export_file, tmpdir, media_root
):
    # given
    file_mock = mock.MagicMock(spec=File)
    file_mock.name = "temp_file.csv"
    data_type = "gift cards"

    user_export_file.content_file = file_mock
    user_export_file.save()

    # when
    notifications.send_export_failed_info(user_export_file, data_type)

    # then
    expected_payload = {
        "export": get_default_export_payload(user_export_file),
        "recipient_email": user_export_file.user.email,
        "data_type": data_type,
        **get_site_context(),
    }

    mocked_notify.assert_called_once_with(
        AdminNotifyEvent.CSV_EXPORT_FAILED, expected_payload
    )
