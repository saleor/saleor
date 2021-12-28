from saleor.settings import *  # noqa F405

LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

INSTALLED_APPS.append("django_celery_results")  # noqa F405
