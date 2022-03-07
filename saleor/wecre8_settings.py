import dj_database_url

from saleor.settings import *  # noqa F405

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
CITIES_LIGHT_TRANSLATION_LANGUAGES = ["ar"]
CITIES_LIGHT_APP_NAME = "provinces"  # noqa F405
CITIES_LIGHT_INCLUDE_COUNTRIES = ["SA", "AE", "OM", "BH", "QA", "KW"]

INSTALLED_APPS += [  # noqa F405
    "cities_light",
    "django_celery_results",
    "saleor.plugins.datamigration",
]

CELERY_BEAT_SCHEDULE.update(  # noqa F405
    {
        "update-oto-access-token": {
            "task": "saleor.plugins.oto.tasks.update_oto_access_token_task",
            "schedule": timedelta(minutes=30),  # noqa F405
        },
    }
)

DATABASES = {
    "default": dj_database_url.config(
        default="postgres://saleor:saleor@localhost:5432/saleor", conn_max_age=600
    ),
    "datamigration": dj_database_url.config(
        conn_max_age=600,
        env="DATAMIGRATION_DATABASE_URL",
    ),
}
