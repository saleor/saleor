from django.conf import settings

from saleor.celeryconf import app
from saleor.core.db.connection import allow_writer


# ruleid: celery-migration-task-missing-dedicated-queue
@app.task
def migration_task_without_queue_set():
    pass


# ruleid: celery-migration-task-missing-dedicated-queue
@app.task
@allow_writer
def migration_task_without_queue_set_and_more_decorators():
    pass


# ruleid: celery-migration-task-missing-dedicated-queue
@app.task()
def migration_task_with_no_args():
    pass


# ruleid: celery-migration-task-missing-dedicated-queue
@app.task(bind=True)
def migration_task_with_arg(self):
    pass


# ruleid: celery-migration-task-missing-dedicated-queue
@app.task(bind=True, retry_backoff=30, retry_kwargs={"max_retries": 5})
def migration_task_with_args_and_kwargs(
    self, brand_data: dict, *, app_installation_id=None, app_id=None
):
    pass


# ruleid: celery-migration-task-missing-dedicated-queue
@app.task(queue="some-queue")
def migration_task_with_queue_set_to_raw_value():
    pass


# ruleid: celery-migration-task-missing-dedicated-queue
@app.task(bind=True, retry_backoff=30, queue="some-queue")
def migration_task_with_args_kwargs_and_queue_set_to_raw_value(self):
    pass


# ok: celery-migration-task-missing-dedicated-queue
@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
def migration_task_with_queue_set():
    pass


# ok: celery-migration-task-missing-dedicated-queue
@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer
def migration_task_with_queue_set_and_more_decorators():
    pass


# ok: celery-migration-task-missing-dedicated-queue
@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME, bind=True)
def migration_task_with_kwargs_and_queue_set_first(self):
    pass


# ok: celery-migration-task-missing-dedicated-queue
@app.task(bind=True, queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
def migration_task_with_kwargs_and_queue_set_last(self):
    pass


# ok: celery-migration-task-missing-dedicated-queue
@app.task(bind=True, queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME, retry_backoff=30)
def migration_task_with_kwargs_and_queue_set_in_the_middle(self):
    pass


# ok: celery-migration-task-missing-dedicated-queue
@app.task(bind=True, queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME, retry_backoff=30)
def migration_task_with_multiline_kwargs_and_queue():
    pass
