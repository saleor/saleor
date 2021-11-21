from saleor.settings import *

LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

PLUGINS.append(
    "saleor.plugins.oto.plugin.OTOPlugin",
)

CELERY_BEAT_SCHEDULE.update(
    {
        "update-oto-access-token": {
            "task": "saleor.plugins.oto.tasks.update_oto_access_token_task",
            "schedule": timedelta(hours=1),
        },
    }
)
