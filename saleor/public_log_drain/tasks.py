from typing import Any

from django.conf import settings

from ..celeryconf import app
from .public_log_drain import LogDrainAttributes, PublicLogDrain
from .transporters import LogDrainTransporter
from .transporters.public_log_drain_http_transporter import LogDrainHTTPTransporter
from .transporters.public_log_drain_otel_transporter import LogDrainOtelTransporter


@app.task
def emit_public_log_task(
    logger_name: str, trace_id: int, span_id: int, attributes: dict[Any, Any]
):
    attributes = LogDrainAttributes(**attributes)
    transports: list[LogDrainTransporter] = []
    if otl_endpoint := settings.OTEL_TRANSPORTED_ENDPOINT:
        transports.append(LogDrainOtelTransporter(endpoint=otl_endpoint))
    if http_endpoint := settings.HTTP_TRANSPORTED_ENDPOINT:
        transports.append(LogDrainHTTPTransporter(endpoint=http_endpoint))
    if not transports:
        return
    PublicLogDrain(transports).emit_log(logger_name, trace_id, span_id, attributes)
