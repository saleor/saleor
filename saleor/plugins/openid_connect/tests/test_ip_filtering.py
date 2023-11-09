import pytest
from django.core import signing
from requests_hardened.ip_filter import InvalidIPAddress

from ....core.http_client import HTTPClient


def test_rejects_private_ips(openid_plugin, id_token, rf, monkeypatch):
    """Ensure private IP addresses are rejected by OIDC."""
    monkeypatch.setattr(HTTPClient.config, "ip_filter_enable", True)

    plugin = openid_plugin(oauth_token_url="https://0.0.0.0")
    oauth_payload = {
        "code": 123,
        "state": signing.dumps({"redirectUri": "https://example.com"}),
    }

    # Should reject the ip address used for the HTTP request.
    with pytest.raises(InvalidIPAddress):
        plugin.external_obtain_access_tokens(oauth_payload, rf.request(), None)
