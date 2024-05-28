from django.utils import timezone
from opentelemetry._logs.severity import SeverityNumber
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs._internal import LogRecord
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.span import TraceFlags

from . import LogDrainTransporter


class LogDrainOtelTransporter(LogDrainTransporter):
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

    def emit(self, attributes):
        log_record = LogRecord(
            timestamp=int(timezone.now().timestamp()),
            observed_timestamp=int(timezone.now().timestamp()),
            trace_id=0,
            span_id=0,
            trace_flags=TraceFlags.DEFAULT,
            severity_text="WARN",
            severity_number=SeverityNumber.WARN,
            body="To moze i nawet dziala!",
            attributes={"dupa1": "New"},
            resource=self.resource,
        )
        self.logger_provider.get_logger("webhooks").emit(log_record)
