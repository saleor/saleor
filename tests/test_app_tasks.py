from unittest.mock import Mock

import pytest
from requests import RequestException

from saleor.app.models import App, AppJob
from saleor.app.tasks import install_app_task
from saleor.core import JobStatus


@pytest.mark.vcr
def test_install_app_task(app_job):
    install_app_task(app_job.id, activate=False)
    assert not AppJob.objects.all().exists()
    app = App.objects.filter(name=app_job.app_name).first()
    assert app
    assert app.is_active is False


@pytest.mark.vcr
def test_install_app_task_wrong_format_of_target_token_url():
    app_job = AppJob.objects.create(
        app_name="External App", manifest_url="http://localhost:3000/manifest-wrong",
    )
    install_app_task(app_job.id, activate=False)
    app_job.refresh_from_db()
    assert app_job.status == JobStatus.FAILED
    assert app_job.message == "token_target_url: ['Incorrect format.']"
    assert not App.objects.all()


@pytest.mark.vcr
def test_install_app_task_request_timeout(monkeypatch, app_job):
    mocked_post = Mock(side_effect=RequestException("Timeout"))
    monkeypatch.setattr("saleor.app.installation_utils.requests.post", mocked_post)
    install_app_task(app_job.pk, activate=True)
    app_job.refresh_from_db()

    assert not App.objects.all().exists()
    assert app_job.status == JobStatus.FAILED
    assert (
        app_job.message
        == "Failed to connect to app. Try later or contact with app support."
    )


@pytest.mark.vcr
def test_install_app_task_wrong_response_code(monkeypatch, app_job):
    app_job = AppJob.objects.create(
        app_name="External App", manifest_url="http://localhost:3000/manifest-wrong1",
    )
    mocked_post = Mock()
    mocked_post.status_code = 404
    monkeypatch.setattr("saleor.app.installation_utils.requests.post", mocked_post)
    install_app_task(app_job.pk, activate=True)
    app_job.refresh_from_db()

    assert not App.objects.all().exists()
    assert app_job.status == JobStatus.FAILED
    assert (
        app_job.message
        == "Failed to connect to app. Try later or contact with app support."
    )


def test_install_app_task_undefined_error(monkeypatch, app_job):
    mock_install_app = Mock(side_effect=Exception("Unknow"))

    monkeypatch.setattr("saleor.app.tasks.install_app", mock_install_app)
    install_app_task(app_job.pk)
    app_job.refresh_from_db()
    assert app_job.status == JobStatus.FAILED
    assert app_job.message == "Unknow error. Contact with app support."
