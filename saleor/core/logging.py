import platform
import time

from .. import __version__ as saleor_version
from celery._state import get_current_task as get_current_celery_task
from pythonjsonlogger.jsonlogger import JsonFormatter as BaseFormatter


class JsonFormatter(BaseFormatter):
    converter = time.gmtime

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["hostname"] = platform.node()
        try:
            log_record["query"] = record.exc_info[1]._exc_query
            log_record["version"] = saleor_version
        except (KeyError, TypeError):
            pass


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


class JsonCeleryTaskFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        task = get_current_celery_task()
        message_dict.update(
            {
                "celeryTaskId": task.request.id,
                "celeryTaskName": task.name,
            }
        )
        super().add_fields(log_record, record, message_dict)
