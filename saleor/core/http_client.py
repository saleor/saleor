from copy import copy
from typing import Any

import requests_hardened
from django.conf import settings
from opentelemetry.instrumentation.utils import suppress_http_instrumentation
from requests import PreparedRequest, Response

from .. import user_agent_version

HTTPConfig = requests_hardened.Config(
    ip_filter_enable=settings.HTTP_IP_FILTER_ENABLED,
    ip_filter_allow_loopback_ips=settings.HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS,
    never_redirect=True,
    default_timeout=settings.COMMON_REQUESTS_TIMEOUT,
    user_agent_override=user_agent_version,
)


class HTTPSession(requests_hardened.HTTPSession):
    """Hardened HTTP session whose requests are not traced by OpenTelemetry instrumentors.

    The OpenTelemetry requests instrumentor opens a CLIENT span for every request and writes that span's context into the `traceparent` header. Library instrumentors write to the global tracer provider and bypass `TELEMETRY_TRACER_CLASS`, so a tracer that exports Saleor's spans elsewhere, for example to app owners, never has that span, and the receiver would get a parent it cannot see. For webhooks the instrumentor would also overwrite the `traceparent` that `send_webhook_using_http` injects for the `webhooks.<event>` span, and the header sent would differ from the one stored in the delivery attempt's `request_headers`. Requests sent through this session therefore carry only the trace context that Saleor injects itself with `tracer.inject_context`, and the Saleor spans around the call represent it.
    """

    def send(self, request: PreparedRequest, **kwargs: Any) -> Response:
        with suppress_http_instrumentation():
            return super().send(request, **kwargs)


class HTTPClientManager(requests_hardened.Manager):
    __slots__ = ()

    def clone(self):
        return HTTPClientManager(config=copy(self.config))

    def get_session(self):
        return HTTPSession(self.config)


HTTPClient = HTTPClientManager(HTTPConfig)
