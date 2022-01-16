from saleor.settings import *  # noqa F405

INSTALLED_APPS.append("django_celery_results")  # noqa F405

CELERY_BEAT_SCHEDULE.update(  # noqa F405
    {
        "update-oto-access-token": {
            "task": "saleor.plugins.oto.tasks.update_oto_access_token_task",
            "schedule": timedelta(hours=1),  # noqa F405
        },
    }
)
