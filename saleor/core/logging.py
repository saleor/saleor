import platform
import time

from celery._state import get_current_task as get_current_celery_task
from pythonjsonlogger.jsonlogger import JsonFormatter as BaseFormatter

from .. import __version__ as saleor_version


class JsonFormatter(BaseFormatter):
    converter = time.gmtime  # type: ignore[assignment]

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["hostname"] = platform.node()
        try:
            log_record["query"] = record.exc_info[1]._exc_query
            log_record["version"] = saleor_version
        except (TypeError, IndexError, AttributeError):
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
        # Similarly to the Celery task formatter, we need to handle the case when `task` is None.
        # https://github.com/celery/celery/blob/main/celery/app/log.py#L31
        task_id = task.request.id if task and task.request else "???"
        task_name = task.name if task else "???"
        message_dict.update(
            {
                "celeryTaskId": task_id,
                "celeryTaskName": task_name,
            }
        )
        super().add_fields(log_record, record, message_dict)
