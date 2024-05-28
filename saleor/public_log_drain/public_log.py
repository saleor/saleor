from django.conf import settings

from .public_log_drain import LogDrainAttributes, PublicLogDrain
from .transporters.public_log_drain_otel_transporter import LogDrainOtelTransporter


def emit_public_log(logger_name: str, trace_id: int, attributes: LogDrainAttributes):
    breakpoint()
    transports = []
    if otl_endpoint := settings.OTEL_TRANSPORTED_ENDPOINT:
        transports.append(LogDrainOtelTransporter(endpoint=otl_endpoint))
    if not transports:
        return
    PublicLogDrain(transports).emit_log(logger_name, trace_id, attributes)
