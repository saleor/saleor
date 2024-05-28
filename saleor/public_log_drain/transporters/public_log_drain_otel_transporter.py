from django.utils import timezone
from opentelemetry._logs.severity import SeverityNumber
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs._internal import LogRecord
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.span import TraceFlags

from ..public_log_drain import LogDrainAttributes, LogLevel
from . import LogDrainTransporter


class LogDrainOtelTransporter(LogDrainTransporter):
    LEVEL_TO_SEVERITY_NUMBER_MAP = {
        LogLevel.INFO: SeverityNumber.INFO,
        LogLevel.WARN: SeverityNumber.WARN,
        LogLevel.ERROR: SeverityNumber.ERROR,
    }

    def __init__(self, endpoint: str):
        if not endpoint:
            raise ValueError("Endpoint is required")

        self.endpoint = endpoint
        self.exporter = OTLPLogExporter(endpoint=self.endpoint)
        self.resource = Resource.create(
            {
                "service.name": "Saleor",
            }
        )

        self.logger_provider = LoggerProvider(resource=self.resource)

        self.logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(self.exporter)
        )

    def get_endpoint(self):
        return self.endpoint

    def emit(self, logger_name: str, trace_id: int, attributes: LogDrainAttributes):
        level = LogDrainAttributes.level
        log_record = LogRecord(
            timestamp=int(timezone.now().timestamp()),
            observed_timestamp=int(timezone.now().timestamp()),
            trace_id=trace_id,
            span_id=0,
            trace_flags=TraceFlags.DEFAULT,
            severity_text="WARN",
            severity_number=self.LEVEL_TO_SEVERITY_NUMBER_MAP[level],
            body=attributes.message,
            attributes={
                "api_url": attributes.api_url,
                "checkout_id": attributes.checkout_id,
                "order_id": attributes.order_id,
            },
            resource=self.resource,
        )
        self.logger_provider.get_logger(logger_name).emit(log_record)
