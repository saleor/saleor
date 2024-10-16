import pytest

from ....app.models import AppInstallation


@pytest.fixture
def app_installation():
    app_installation = AppInstallation.objects.create(
        app_name="External App",
        manifest_url="http://localhost:3000/manifest",
    )
    return app_installation
