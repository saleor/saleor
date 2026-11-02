from unittest.mock import patch

import pytest
import requests_hardened
from requests import Request, Response
from requests.adapters import HTTPAdapter
from requests_hardened.ip_filter import InvalidIPAddress

from ... import user_agent_version
from ...plugins.openid_connect.client import OAuth2Client
from ..http_client import HTTPClient, HTTPConfig
from ..telemetry import tracer


def test_user_agent_override():
    # given
    request = Request("GET", "http://www.example.com")
    session = requests_hardened.HTTPSession(HTTPConfig)

    assert request.headers.get("User-Agent") is None

    # when
    session.prepare_request(request)

    # then
    assert request.headers.get("User-Agent") == user_agent_version


@pytest.mark.vcr(match_on=["method", "scheme", "port", "path", "query"])
@pytest.mark.parametrize("protocol", ["https", "http"])
def test_http_client_disallows_private_ip_ranges(protocol):
    """Ensure requests made to private IP address ranges leads to an error to be raised.

    This test ensures that the requests-hardened library works correctly,
    especially when using untested 'requests' and 'urllib3' versions
    that may potentially be unsupported by this library.
    """

    # Enable IP filtering (disabled by default in tests)
    http_manager = HTTPClient.clone()
    http_manager.config.ip_filter_enable = True  # Block private ranges.

    # Should reject the IP address (expect error to be raised)
    with pytest.raises(InvalidIPAddress, match="10.0.0.1"):
        http_manager.send_request("GET", f"{protocol}://10.0.0.1", timeout=0.1)

    # Should not reject public IP ranges (sanity check).
    response = http_manager.send_request("GET", f"{protocol}://example.com")
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("_case", "get_session"),
    [
        ("http_client", HTTPClient.get_session),
        ("cloned_http_client", lambda: HTTPClient.clone().get_session()),
        (
            "oauth2_client",
            lambda: OAuth2Client(
                token={"access_token": "token", "token_type": "Bearer"}
            ),
        ),
    ],
)
@patch.object(HTTPAdapter, "send")
def test_http_session_is_not_traced_by_requests_instrumentor(
    mocked_adapter_send, _case, get_session, requests_instrumentor, get_test_spans
):
    # given
    assert requests_instrumentor.is_instrumented_by_opentelemetry is True
    server_response = Response()
    server_response.status_code = 200
    mocked_adapter_send.return_value = server_response

    # when
    with tracer.start_as_current_span("outgoing_call"), get_session() as session:
        session.request("GET", "https://example.com")

    # then
    sent_request = mocked_adapter_send.call_args.args[0]
    assert "traceparent" not in sent_request.headers
    assert [span.name for span in get_test_spans()] == ["outgoing_call"]
