import datetime
from unittest.mock import ANY, MagicMock, Mock, patch

import pytz
from django.core.files import File
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from ...core import JobStatus
from .. import ExportEvents, FileTypes
from ..models import ExportEvent, ExportFile
from ..tasks import (
    ExportTask,
    delete_old_export_files,
    export_gift_cards_task,
    export_products_task,
)


@patch("saleor.csv.tasks.export_products")
def test_export_products_task(export_products_mock, user_export_file):
    # given
    scope = {"all": ""}
    export_info = {"fields": "name"}
    file_type = FileTypes.CSV
    delimiter = ";"

    # when
    export_products_task(user_export_file.id, scope, export_info, file_type, delimiter)

    # then
    export_products_mock.assert_called_once_with(
        user_export_file, scope, export_info, file_type, delimiter
    )


@patch("saleor.csv.tasks.send_export_failed_info")
@patch("saleor.csv.tasks.export_products")
def test_export_products_task_failed(
    export_products_mock, send_export_failed_info_mock, user_export_file
):
    # given
    scope = {"all": ""}
    export_info = {"fields": "name"}
    file_type = FileTypes.CSV
    delimiter = ";"

    exc_message = "Test error"
    export_products_mock.side_effect = Exception(exc_message)

    # when
    export_products_task.delay(
        user_export_file.id, scope, export_info, file_type, delimiter
    )

    # then
    send_export_failed_info_mock.assert_called_once_with(user_export_file, "products")


@patch("saleor.csv.tasks.export_gift_cards")
def test_export_gift_cards_task(export_gift_cards_mock, user_export_file):
    # given
    scope = {"all": ""}
    file_type = FileTypes.CSV
    delimiter = ";"

    # when
    export_gift_cards_task(user_export_file.id, scope, file_type, delimiter)

    # then
    export_gift_cards_mock.assert_called_once_with(
        user_export_file, scope, file_type, delimiter
    )


@patch("saleor.csv.tasks.send_export_failed_info")
@patch("saleor.csv.tasks.export_gift_cards")
def test_export_gift_cards_task_failed(
    export_gift_cards_mock, send_export_failed_info_mock, user_export_file
):
    # given
    scope = {"all": ""}
    file_type = FileTypes.CSV
    delimiter = ";"

    exc_message = "Test error"
    export_gift_cards_mock.side_effect = Exception(exc_message)

    # when
    export_gift_cards_task.delay(user_export_file.id, scope, file_type, delimiter)

    # then
    send_export_failed_info_mock.assert_called_once_with(user_export_file, "gift cards")


@patch("saleor.csv.tasks.send_export_failed_info")
def test_on_task_failure(send_export_failed_info_mock, user_export_file):
    # given
    exc = Exception("Test")
    task_id = "task_id"
    args = [user_export_file.pk, {"all": ""}]
    kwargs = {}
    info_type = "Test error"
    info = Mock(type=info_type)

    assert user_export_file.status == JobStatus.PENDING
    assert user_export_file.created_at
    previous_updated_at = user_export_file.updated_at

    with freeze_time(datetime.datetime.now()) as frozen_datetime:
        # when
        ExportTask().on_failure(exc, task_id, args, kwargs, info)

        # then
        user_export_file.refresh_from_db()
        assert user_export_file.updated_at == pytz.utc.localize(frozen_datetime())

    assert user_export_file.updated_at != previous_updated_at
    assert user_export_file.status == JobStatus.FAILED
    assert user_export_file.created_at
    assert user_export_file.updated_at != previous_updated_at
    export_failed_event = ExportEvent.objects.get(
        export_file=user_export_file,
        user=user_export_file.user,
        app=None,
        type=ExportEvents.EXPORT_FAILED,
    )
    assert export_failed_event.parameters == {
        "message": str(exc),
        "error_type": info_type,
    }

    send_export_failed_info_mock.assert_called_once_with(user_export_file, ANY)


@patch("saleor.csv.tasks.send_export_failed_info")
def test_on_task_failure_for_app(send_export_failed_info_mock, app_export_file):
    # given
    exc = Exception("Test")
    task_id = "task_id"
    args = [app_export_file.pk, {"all": ""}]
    kwargs = {}
    info_type = "Test error"
    info = Mock(type=info_type)

    assert app_export_file.status == JobStatus.PENDING
    assert app_export_file.created_at
    previous_updated_at = app_export_file.updated_at

    with freeze_time(datetime.datetime.now()) as frozen_datetime:
        # when
        ExportTask().on_failure(exc, task_id, args, kwargs, info)

        # then
        app_export_file.refresh_from_db()
        assert app_export_file.updated_at == pytz.utc.localize(frozen_datetime())

    assert app_export_file.updated_at != previous_updated_at
    assert app_export_file.status == JobStatus.FAILED
    assert app_export_file.created_at
    assert app_export_file.updated_at != previous_updated_at
    export_failed_event = ExportEvent.objects.get(
        export_file=app_export_file,
        user=None,
        app=app_export_file.app,
        type=ExportEvents.EXPORT_FAILED,
    )
    assert export_failed_event.parameters == {
        "message": str(exc),
        "error_type": info_type,
    }

    send_export_failed_info_mock.called_once_with(app_export_file, ANY)


def test_on_task_success(user_export_file):
    # given
    task_id = "task_id"
    args = [user_export_file.pk, {"filter": {}}]
    kwargs = {}

    assert user_export_file.status == JobStatus.PENDING
    assert user_export_file.created_at
    previous_updated_at = user_export_file.updated_at

    with freeze_time(datetime.datetime.now()) as frozen_datetime:
        # when
        ExportTask().on_success(None, task_id, args, kwargs)

        # then
        user_export_file.refresh_from_db()
        assert user_export_file.updated_at == pytz.utc.localize(frozen_datetime())
        assert user_export_file.updated_at != previous_updated_at

    assert user_export_file.status == JobStatus.SUCCESS
    assert user_export_file.created_at
    assert ExportEvent.objects.filter(
        export_file=user_export_file,
        user=user_export_file.user,
        type=ExportEvents.EXPORT_SUCCESS,
    )


@override_settings(EXPORT_FILES_TIMEDELTA=datetime.timedelta(days=5))
@patch("django.core.files.storage.default_storage.exists", lambda x: True)
@patch("django.core.files.storage.default_storage.delete")
def test_delete_old_export_files(default_storage_delete_mock, staff_user):
    # given
    now = timezone.now()
    expired_success_file_1_mock = MagicMock(spec=File)
    expired_success_file_1_mock.name = "expired_success_1.csv"

    expired_success_file_2_mock = MagicMock(spec=File)
    expired_success_file_2_mock.name = "expired_success_1.csv"

    not_expired_success_file_mock = MagicMock(spec=File)
    not_expired_success_file_mock.name = "not_expired_success.csv"

    export_file_list = list(
        ExportFile.objects.bulk_create(
            [
                ExportFile(
                    user=staff_user,
                    status=JobStatus.SUCCESS,
                ),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.SUCCESS,
                ),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.SUCCESS,
                ),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.PENDING,
                ),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.PENDING,
                ),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.FAILED,
                ),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.FAILED,
                ),
            ]
        )
    )

    expired_success_1, not_expired_success, expired_success_2 = (
        export_file_list[0],
        export_file_list[1],
        export_file_list[2],
    )
    expired_success_1.content_file = expired_success_file_1_mock
    expired_success_2.content_file = expired_success_file_2_mock
    not_expired_success.content_file = not_expired_success_file_mock

    ExportFile.objects.bulk_update(export_file_list[:3], ["content_file"])

    expired_export_files = export_file_list[::2]
    expired_export_events = [
        ExportEvent(
            type=ExportEvents.EXPORT_PENDING,
            date=now - datetime.timedelta(days=6),
            export_file=export_file,
        )
        for export_file in expired_export_files
    ]
    not_expired_export_files = export_file_list[1::2]
    not_expired_export_events = [
        ExportEvent(
            type=ExportEvents.EXPORT_PENDING,
            date=now - datetime.timedelta(days=2),
            export_file=export_file,
        )
        for export_file in not_expired_export_files
    ]

    ExportEvent.objects.bulk_create(expired_export_events + not_expired_export_events)
    export_file_with_no_events = ExportFile.objects.create(
        user=staff_user, status=JobStatus.SUCCESS
    )
    expired_export_files.append(export_file_with_no_events)

    # when
    delete_old_export_files()

    # then
    assert default_storage_delete_mock.call_count == 2
    assert {
        arg for call in default_storage_delete_mock.call_args_list for arg in call.args
    } == {expired_success_file_1_mock.name, expired_success_file_2_mock.name}
    assert not ExportFile.objects.filter(
        id__in=[export_file.id for export_file in expired_export_files]
    )
    assert len(
        ExportFile.objects.filter(
            id__in=[export_file.id for export_file in not_expired_export_files]
        )
    ) == len(not_expired_export_files)
