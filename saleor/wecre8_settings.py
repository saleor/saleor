from saleor.settings import *  # noqa F405

LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

PLUGINS.append(  # noqa F405
    "saleor.plugins.oto.plugin.OTOPlugin",
)

INSTALLED_APPS.append("django_celery_results")  # noqa F405

CELERY_BEAT_SCHEDULE.update(  # noqa F405
    {
        "update-oto-access-token": {
            "task": "saleor.plugins.oto.tasks.update_oto_access_token_task",
            "schedule": timedelta(hours=1),  # noqa F405
        },
    }
)
