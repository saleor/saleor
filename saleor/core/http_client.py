import requests_hardened
from django.conf import settings

from .. import user_agent_version

HTTPConfig = requests_hardened.Config(
    ip_filter_enable=settings.HTTP_IP_FILTER_ENABLED,
    ip_filter_allow_loopback_ips=settings.HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS,
    never_redirect=True,
    default_timeout=settings.COMMON_REQUESTS_TIMEOUT,
    user_agent_override=user_agent_version,
)

HTTPClient = requests_hardened.Manager(HTTPConfig)
