from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .transporters import LogDrainTransporter


class LogType(Enum):
    WEBHOOK_SENT = "WEBHOOK_SENT"
    WEBHOOK_RESPONSE_RECEIVED = "WEBHOOK"
    WEBHOOK_RETRIED = "WEBHOOK_RETRIED"


class LogLevel(Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class LogDrainAttributes:
    type: str  # LogType
    level: str  # LogLevel
    api_url: str
    message: str
    version: str
    checkout_id: Optional[str] = None
    order_id: Optional[str] = None


class PublicLogDrain:
    def __init__(self, transporters=None):
        if transporters is None:
            transporters = []
        self.transporters: list[LogDrainTransporter] = transporters

    def add_transporter(self, transporter):
        self.transporters.append(transporter)

    def emit_log(self, logger_name: str, trace_id: int, attributes: LogDrainAttributes):
        for transporter in self.transporters:
            transporter.emit(logger_name, trace_id, attributes)

    def get_transporters(self):
        return self.transporters
