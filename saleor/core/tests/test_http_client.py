import requests_hardened
from django.conf import settings
from requests import Request

from ... import user_agent_version

HTTPConfig = requests_hardened.Config(
    ip_filter_enable=settings.HTTP_IP_FILTER_ENABLED,
    ip_filter_allow_loopback_ips=settings.HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS,
    never_redirect=True,
    default_timeout=(2, 10),
    user_agent_override=user_agent_version,
)


def test_user_agent_override():
    # given
    request = Request("GET", "http://www.example.com")
    session = requests_hardened.HTTPSession(HTTPConfig)

    assert request.headers.get("User-Agent") is None

    # when
    session.prepare_request(request)

    # then
    assert request.headers.get("User-Agent") == user_agent_version
