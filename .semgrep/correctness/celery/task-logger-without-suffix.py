import logging
from celery.utils.log import get_task_logger

def same_name_using___name__():
    # Using the same name (__name__) should match.
    # ruleid: task-logger-without-suffix
    logger = logging.getLogger(__name__)
    task_logger = get_task_logger(__name__)

def same_name_with_celery_first():
    # Using the same name (__name__) should match,
    # even if get_task_logger() is called before logging.getLogger().
    # ruleid: task-logger-without-suffix
    task_logger = get_task_logger(__name__)
    logger = logging.getLogger(__name__)

def different_name_get_task_logger():
    # Using a different name in `get_task_logger()` shouldn't match.
    # ok: task-logger-without-suffix
    task_logger = get_task_logger(f"{__name__}.celery")

def different_name_logging_getlogger():
    # Using a different name in logging.getLogger shouldn't match.
    # ok: task-logger-without-suffix
    logger = logging.getLogger("foo")
    task_logger = get_task_logger(__name__)

def same_name_hardcoded():
    # Using the same name as a string literal should match.
    # ruleid: task-logger-without-suffix
    logger = logging.getLogger("foo")
    task_logger = get_task_logger("foo")

def same_name_without_variables():
    # Using the same name without creating variables should match.
    # ruleid: task-logger-without-suffix
    logging.getLogger("foo")
    get_task_logger("foo")

