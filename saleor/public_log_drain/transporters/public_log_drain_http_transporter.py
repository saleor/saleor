from django.urls import reverse
from django.utils import timezone

from ...app.headers import AppHeaders
from ...core.http_client import HTTPClient
from ...core.utils import build_absolute_uri
from ..public_log_drain import LogDrainAttributes
from . import LogDrainTransporter


class LogDrainHTTPTransporter(LogDrainTransporter):
    def __init__(self, endpoint: str):
        if not endpoint:
            raise ValueError("Endpoint is required")

        self.headers = {
            "Content-Type": "application/json",
            AppHeaders.DOMAIN: build_absolute_uri(reverse("api")),
        }

        self.endpoint = endpoint

    def get_endpoint(self):
        return self.endpoint

    def get_payload(self, trace_id: int, attributes: LogDrainAttributes):
        data = attributes.__dict__
        data.update(
            timestamp=int(timezone.now().timestamp()),
            trace_id=trace_id,
        )
        return data

    def emit(
        self,
        logger_name: str,
        trace_id: int,
        span_id: int,
        attributes: LogDrainAttributes,
    ):
        HTTPClient.send_request(
            "POST",
            self.get_endpoint(),
            json=self.get_payload(trace_id, attributes),
            headers=self.headers,
            allow_redirects=False,
        )
