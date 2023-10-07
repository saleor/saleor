import requests_hardened
from django.conf import settings

HTTPConfig = requests_hardened.Config(
    ip_filter_enable=settings.HTTP_IP_FILTER_ENABLED,
    ip_filter_allow_localhost=settings.HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS,
    never_allow_redirects=True,
    default_timeout=settings.COMMON_REQUESTS_TIMEOUT,
)

HTTPClient = requests_hardened.Manager(HTTPConfig)
