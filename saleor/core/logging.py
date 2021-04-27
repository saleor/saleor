import platform
import time

from pythonjsonlogger.jsonlogger import JsonFormatter as BaseFormatter


class JsonFormatter(BaseFormatter):
    converter = time.gmtime

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["hostname"] = platform.node()


class JsonCeleryFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        message_dict.update(
            {
                "celeryTaskId": record.data.get("id"),
                "celeryTaskName": record.data.get("name"),
                "celeryTaskRuntime": record.data.get("runtime"),
            }
        )
        super().add_fields(log_record, record, message_dict)
        log_record.pop("data")
