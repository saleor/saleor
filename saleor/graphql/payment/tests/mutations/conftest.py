import pytest

from .....app.models import App


@pytest.fixture
def transaction_request_webhook(permission_manage_payments):
    app = App.objects.create(
        name="Sample app objects",
        is_active=True,
        identifier="saleor.app.payment",
    )
    app.permissions.set([permission_manage_payments])
    webhook = app.webhooks.create(
        name="Request", is_active=True, target_url="http://localhost:8000/endpoint/"
    )

    return webhook
