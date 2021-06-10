import platform
import time

import opentracing
from pythonjsonlogger.jsonlogger import JsonFormatter as BaseFormatter


class JsonFormatter(BaseFormatter):
    converter = time.gmtime

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["hostname"] = platform.node()
        # Add tracing info to logs for Datadog
        active_span = opentracing.global_tracer().active_span
        span_id = 0
        trace_id = 0
        if active_span:
            span_id = active_span.context.span_id
            trace_id = active_span.context.trace_id
        log_record["dd"] = {"trace_id": trace_id, "span_id": span_id}

