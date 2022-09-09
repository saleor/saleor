from unittest.mock import Mock

import pytest
from requests import RequestException

from ...core import JobStatus
from ..installation_utils import AppInstallationError
from ..models import App, AppInstallation
from ..tasks import install_app_task


@pytest.mark.vcr
def test_install_app_task(app_installation):
    install_app_task(app_installation.id, activate=False)
    assert not AppInstallation.objects.all().exists()
    app = App.objects.filter(name=app_installation.app_name).first()
    assert app
    assert app.is_active is False


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
    monkeypatch.setattr("saleor.app.installation_utils.requests.post", mocked_post)
    install_app_task(app_installation.pk, activate=True)
    app_installation.refresh_from_db()

    assert not App.objects.all().exists()
    assert app_installation.status == JobStatus.FAILED
    assert (
        app_installation.message
        == "Failed to connect to app. Try later or contact with app support."
    )


@pytest.mark.vcr
def test_install_app_task_wrong_response_code(monkeypatch):
    app_installation = AppInstallation.objects.create(
        app_name="External App",
        manifest_url="http://localhost:3000/manifest-wrong1",
    )
    response_status_code = 404
    mocked_post = Mock()
    mocked_post.status_code = response_status_code
    monkeypatch.setattr("saleor.app.installation_utils.requests.post", mocked_post)
    message = (
        f"App internal error ({response_status_code}). "
        "Try later or contact with app support."
    )

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
