import pytest

from ....webhook.observability import WebhookData


@pytest.fixture
def observability_webhook_data(observability_webhook):
    return WebhookData(
        id=observability_webhook.id,
        saleor_domain="mirumee.com",
        target_url=observability_webhook.target_url,
        secret_key=observability_webhook.secret_key,
    )
