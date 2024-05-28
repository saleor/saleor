import logging
from unittest.mock import ANY, Mock

import pytest
from django.utils import timezone
from requests import RequestException
from requests_hardened import HTTPSession

from ...core import JobStatus
from ...core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from ...webhook.models import Webhook
from ..installation_utils import AppInstallationError
from ..models import App, AppExtension, AppInstallation, AppToken
from ..tasks import install_app_task, remove_apps_task


@pytest.mark.vcr
def test_install_app_task(app_installation):
    install_app_task(app_installation.id, activate=False)
    assert not AppInstallation.objects.all().exists()
    app = App.objects.filter(name=app_installation.app_name).first()
    assert app
    assert app.is_active is False
    assert app.is_installed


def test_install_app_task_job_id_does_not_exist(caplog):
    # given
    nonexistent_job_id = 5435435345

    # when
    install_app_task(nonexistent_job_id, activate=True)

    # then
    assert not App.objects.exists()
    assert caplog.record_tuples == [
        (
            ANY,
            logging.WARNING,
            "Failed to install app. AppInstallation not found for job_id: "
            f"{nonexistent_job_id}.",
        )
    ]


@pytest.mark.vcr
def test_install_app_task_wrong_format_of_target_token_url():
    app_installation = AppInstallation.objects.create(
        app_name="External App",
        manifest_url="http://localhost:3000/manifest-wrong",
    )
    install_app_task(app_installation.id, activate=False)
    app_installation.refresh_from_db()
    assert app_installation.status == JobStatus.FAILED
    assert app_installation.message == "tokenTargetUrl: ['Incorrect format.']"
    assert not App.objects.all()


@pytest.mark.vcr
def test_install_app_task_request_timeout(monkeypatch, app_installation):
    mocked_post = Mock(side_effect=RequestException("Timeout"))
    monkeypatch.setattr(HTTPSession, "request", mocked_post)
    install_app_task(app_installation.pk, activate=True)
    app_installation.refresh_from_db()

    assert not App.objects.all().exists()
    assert app_installation.status == JobStatus.FAILED
    assert (
        app_installation.message
        == "Failed to connect to app. Try later or contact with app support."
    )


@pytest.mark.vcr
def test_install_app_task_wrong_response_code():
    app_installation = AppInstallation.objects.create(
        app_name="External App",
        manifest_url="http://localhost:3000/manifest-wrong1",
    )
    message = "App internal error (404). Try later or contact with app support."

    install_app_task(app_installation.pk, activate=True)
    app_installation.refresh_from_db()

    assert not App.objects.all().exists()
    assert app_installation.status == JobStatus.FAILED
    assert app_installation.message == message


def test_install_app_task_installation_error(monkeypatch, app_installation):
    error_msg = "App installation error."
    mock_install_app = Mock(side_effect=AppInstallationError(error_msg))
    monkeypatch.setattr("saleor.app.tasks.install_app", mock_install_app)

    install_app_task(app_installation.pk)

    app_installation.refresh_from_db()
    assert app_installation.status == JobStatus.FAILED
    assert app_installation.message == error_msg


def test_install_app_task_undefined_error(monkeypatch, app_installation):
    mock_install_app = Mock(side_effect=Exception("Unknow"))

    monkeypatch.setattr("saleor.app.tasks.install_app", mock_install_app)
    install_app_task(app_installation.pk)
    app_installation.refresh_from_db()
    assert app_installation.status == JobStatus.FAILED
    assert app_installation.message == "Unknown error. Contact with app support."


# Saleor should use `transaction=True` to check if IntegrityError is not raised.
# IntegrityError is raised when we try to remove app with related objects.
# Without `transaction=True` test will pass due to be in one atomic bloc.
@pytest.mark.django_db(transaction=True)
def test_remove_app_task(
    event_attempt_removed_app, removed_app_with_extensions, removed_app
):
    # given
    removed_app.tokens.create(name="token1")
    assert App.objects.count() > 0
    assert AppToken.objects.count() > 0
    assert AppExtension.objects.count() > 0
    assert Webhook.objects.count() > 0
    assert EventDelivery.objects.count() > 0
    assert EventPayload.objects.count() > 0
    assert EventDeliveryAttempt.objects.count() > 0

    # when
    remove_apps_task()

    # then
    assert App.objects.count() == 0
    assert AppToken.objects.count() == 0
    assert AppExtension.objects.count() == 0
    assert Webhook.objects.count() == 0
    assert EventDelivery.objects.count() == 0
    assert EventPayload.objects.count() == 0
    assert EventDeliveryAttempt.objects.count() == 0


def test_remove_app_task_not_remove_not_own_payloads(
    event_attempt_removed_app,
):
    # given
    EventPayload.objects.create(payload="")
    assert EventPayload.objects.count() == 2

    # when
    remove_apps_task()

    # then
    assert EventPayload.objects.count() == 1


def test_remove_app_task_no_app_to_remove(app):
    # given
    assert App.objects.count() == 1

    # when
    remove_apps_task()

    # then
    assert App.objects.count() == 1


def test_remove_app_task_delete_period_in_progress():
    # given
    App.objects.create(name="App", is_active=True, removed_at=timezone.now())
    assert App.objects.count() == 1

    # when
    remove_apps_task()

    # then
    assert App.objects.count() == 1
