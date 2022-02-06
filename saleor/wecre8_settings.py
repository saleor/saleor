from saleor.settings import *  # noqa F405

CITIES_LIGHT_TRANSLATION_LANGUAGES = ["ar"]
CITIES_LIGHT_INCLUDE_COUNTRIES = ["SA"]
CITIES_LIGHT_INCLUDE_CITY_TYPES = [
    "PPL",
    "PPLA",
    "PPLA2",
    "PPLA3",
    "PPLA4",
    "PPLC",
    "PPLF",
    "PPLG",
    "PPLL",
    "PPLR",
    "PPLS",
    "STLMT",
]
CITIES_LIGHT_APP_NAME = "provinces"  # noqa F405
INSTALLED_APPS = ["cities_light", "django_celery_results", *INSTALLED_APPS]  # noqa F405

CELERY_BEAT_SCHEDULE.update(  # noqa F405
    {
        "update-oto-access-token": {
            "task": "saleor.plugins.oto.tasks.update_oto_access_token_task",
            "schedule": timedelta(minutes=30),  # noqa F405
        },
    }
)
