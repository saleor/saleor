from unittest import mock

import pytest
import requests

from saleor.extensions.manager import get_extensions_manager


@pytest.mark.vcr
@mock.patch(
    "saleor.extensions.plugins.webhook.tasks.requests.post", wraps=requests.post
)
def test_trigger_webhooks_for_event(
    mock_request, webhook, settings, order_with_lines, permission_manage_orders
):
    webhook.service_account.permissions.add(permission_manage_orders)
    webhook.target_url = "https://webhook.site/f0fc9979-cbd4-47b7-8705-1acb03fff1d0"
    webhook.save()
    settings.PLUGINS = ["saleor.extensions.plugins.webhook.plugin.WebhookPlugin"]

    # data = serialize("json", [order_with_lines])
    manager = get_extensions_manager(plugins=settings.PLUGINS)
    manager.postprocess_order_creation(order_with_lines)

    assert mock_request.assert_called_with
    # FIXME validate request.post args
