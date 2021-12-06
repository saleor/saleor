from saleor.settings import *  # noqa F403

LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

PLUGINS += [  # noqa F405
    "saleor.plugins.algolia.plugin.AlgoliaPlugin",
]

INSTALLED_APPS += [  # noqa F405
    "django_celery_results",
]
