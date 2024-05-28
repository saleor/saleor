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
    type: LogType
    level: LogLevel
    api_url: str
    message: str
    checkout_id: Optional[str]
    order_id: Optional[str]


class PublicLogDrain:
    def __init__(self):
        self.transporters: list[LogDrainTransporter] = []

    def add_transporter(self, transporter):
        self.transporters.append(transporter)

    def emit_log(self, logger_name: str, trace_id: int, attributes: LogDrainAttributes):
        for transporter in self.transporters:
            transporter.emit(logger_name, trace_id, attributes)

    def get_transporters(self):
        return self.transporters
