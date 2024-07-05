import ast
import logging
import os
import os.path
import warnings
from datetime import timedelta
from typing import Optional
from urllib.parse import urlparse

import dj_database_url
import dj_email_url
import django_cache_url
import django_stubs_ext
import jaeger_client.config
import pkg_resources
import sentry_sdk
import sentry_sdk.utils
from celery.schedules import crontab
from django.conf import global_settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from django.core.validators import URLValidator
from graphql.execution import executor
from pytimeparse import parse
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger

from . import PatchedSubscriberExecutionContext, __version__
from .core.languages import LANGUAGES as CORE_LANGUAGES
from .core.schedules import initiated_promotion_webhook_schedule
from .graphql.executor import patch_executor

django_stubs_ext.monkeypatch()


def get_list(text):
    return [item.strip() for item in text.split(",")]


def get_bool_from_env(name, default_value):
    if name in os.environ:
        value = os.environ[name]
        try:
            return ast.literal_eval(value)
        except ValueError as e:
            raise ValueError(f"{value} is an invalid value for {name}") from e
    return default_value


def get_url_from_env(name, *, schemes=None) -> Optional[str]:
    if name in os.environ:
        value = os.environ[name]
        message = f"{value} is an invalid value for {name}"
        URLValidator(schemes=schemes, message=message)(value)
        return value
    return None


DEBUG = get_bool_from_env("DEBUG", True)

SITE_ID = 1

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

ROOT_URLCONF = "saleor.urls"

WSGI_APPLICATION = "saleor.wsgi.application"

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

APPEND_SLASH = False

_DEFAULT_CLIENT_HOSTS = "localhost,127.0.0.1"

ALLOWED_CLIENT_HOSTS = os.environ.get("ALLOWED_CLIENT_HOSTS")
if not ALLOWED_CLIENT_HOSTS:
    if DEBUG:
        ALLOWED_CLIENT_HOSTS = _DEFAULT_CLIENT_HOSTS
    else:
        raise ImproperlyConfigured(
            "ALLOWED_CLIENT_HOSTS environment variable must be set when DEBUG=False."
        )

ALLOWED_CLIENT_HOSTS = get_list(ALLOWED_CLIENT_HOSTS)

INTERNAL_IPS = get_list(os.environ.get("INTERNAL_IPS", "127.0.0.1"))

# Maximum time in seconds Django can keep the database connections opened.
# Set the value to 0 to disable connection persistence, database connections
# will be closed after each request.
DB_CONN_MAX_AGE = int(os.environ.get("DB_CONN_MAX_AGE", 600))

DATABASE_CONNECTION_DEFAULT_NAME = "default"
# TODO: For local envs will be activated in separate PR.
# We need to update docs an saleor platform.
# This variable should be set to `replica`
DATABASE_CONNECTION_REPLICA_NAME = "replica"

DATABASES = {
    DATABASE_CONNECTION_DEFAULT_NAME: dj_database_url.config(
        default="postgres://saleor:saleor@localhost:5432/saleor",
        conn_max_age=DB_CONN_MAX_AGE,
    ),
    DATABASE_CONNECTION_REPLICA_NAME: dj_database_url.config(
        default="postgres://saleor:saleor@localhost:5432/saleor",
        # TODO: We need to add read only user to saleor platform,
        # and we need to update docs.
        # default="postgres://saleor_read_only:saleor@localhost:5432/saleor",
        conn_max_age=DB_CONN_MAX_AGE,
        test_options={"MIRROR": DATABASE_CONNECTION_DEFAULT_NAME},
    ),
}

DATABASE_ROUTERS = ["saleor.core.db_routers.PrimaryReplicaRouter"]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

TIME_ZONE = "UTC"
LANGUAGE_CODE = "en"
LANGUAGES = CORE_LANGUAGES
LOCALE_PATHS = [os.path.join(PROJECT_ROOT, "locale")]
USE_I18N = True
USE_L10N = True
USE_TZ = True

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

EMAIL_URL = os.environ.get("EMAIL_URL")
SENDGRID_USERNAME = os.environ.get("SENDGRID_USERNAME")
SENDGRID_PASSWORD = os.environ.get("SENDGRID_PASSWORD")
if not EMAIL_URL and SENDGRID_USERNAME and SENDGRID_PASSWORD:
    EMAIL_URL = (
        f"smtp://{SENDGRID_USERNAME}"
        f":{SENDGRID_PASSWORD}@smtp.sendgrid.net:587/?tls=True"
    )

email_config = dj_email_url.parse(EMAIL_URL or "")

EMAIL_FILE_PATH: str = email_config.get("EMAIL_FILE_PATH", "")
EMAIL_HOST_USER: str = email_config.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD: str = email_config.get("EMAIL_HOST_PASSWORD", "")
EMAIL_HOST: str = email_config.get("EMAIL_HOST", "")
EMAIL_PORT: str = str(email_config.get("EMAIL_PORT", ""))
EMAIL_BACKEND: str = email_config.get("EMAIL_BACKEND", "")
EMAIL_USE_TLS: bool = email_config.get("EMAIL_USE_TLS", False)
EMAIL_USE_SSL: bool = email_config.get("EMAIL_USE_SSL", False)

# SMTP configuration for UserEmailPlugin can be achieved by setting USER_EMAIL_URL.
# Providing that variable means that SMTP configuration for this plugin is not required.
user_email_config = dj_email_url.parse(os.environ.get("USER_EMAIL_URL", ""))

USER_EMAIL_HOST_USER: str = user_email_config.get("EMAIL_HOST_USER") or ""
USER_EMAIL_HOST_PASSWORD: str = user_email_config.get("EMAIL_HOST_PASSWORD") or ""
USER_EMAIL_HOST: str = user_email_config.get("EMAIL_HOST") or ""
USER_EMAIL_PORT: str = str(user_email_config.get("EMAIL_PORT") or "")

USER_EMAIL_USE_TLS: bool = user_email_config.get("EMAIL_USE_TLS", False)
USER_EMAIL_USE_SSL: bool = user_email_config.get("EMAIL_USE_SSL", False)

ENABLE_SSL: bool = get_bool_from_env("ENABLE_SSL", False)

# URL on which Saleor is hosted (e.g., https://api.example.com/). This has precedence
# over ENABLE_SSL and Shop.domain when generating URLs pointing to itself.
PUBLIC_URL: Optional[str] = get_url_from_env("PUBLIC_URL", schemes=["http", "https"])
if PUBLIC_URL:
    if os.environ.get("ENABLE_SSL") is not None:
        warnings.warn("ENABLE_SSL is ignored on URL generation if PUBLIC_URL is set.")
    ENABLE_SSL = urlparse(PUBLIC_URL).scheme.lower() == "https"

if ENABLE_SSL:
    SECURE_SSL_REDIRECT = not DEBUG

DEFAULT_FROM_EMAIL: str = os.environ.get(
    "DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "noreply@example.com"
)

MEDIA_ROOT: str = os.path.join(PROJECT_ROOT, "media")
MEDIA_URL: str = os.environ.get("MEDIA_URL", "/media/")

STATIC_ROOT: str = os.path.join(PROJECT_ROOT, "static")
STATIC_URL: str = os.environ.get("STATIC_URL", "/static/")
STATICFILES_DIRS = [
    ("images", os.path.join(PROJECT_ROOT, "saleor", "static", "images"))
]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

context_processors = [
    "django.template.context_processors.debug",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "saleor.site.context_processors.site",
]

loaders = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": context_processors,
            "loaders": loaders,
            "string_if_invalid": '<< MISSING VARIABLE "%s" >>' if DEBUG else "",
        },
    }
]

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get("SECRET_KEY")

# Additional password algorithms that can be used by Saleor.
# The first algorithm defined by Django is the preferred one; users not using the
# first algorithm will automatically be upgraded to it upon login
PASSWORD_HASHERS = [
    *global_settings.PASSWORD_HASHERS,
    "django.contrib.auth.hashers.BCryptPasswordHasher",
    "saleor.core.hashers.SHA512Base64PBKDF2PasswordHasher",
]

if not SECRET_KEY and DEBUG:
    warnings.warn("SECRET_KEY not configured, using a random temporary key.")
    SECRET_KEY = get_random_secret_key()

RSA_PRIVATE_KEY = os.environ.get("RSA_PRIVATE_KEY", None)
RSA_PRIVATE_PASSWORD = os.environ.get("RSA_PRIVATE_PASSWORD", None)
JWT_MANAGER_PATH = os.environ.get(
    "JWT_MANAGER_PATH", "saleor.core.jwt_manager.JWTManager"
)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "saleor.core.middleware.jwt_refresh_token_middleware",
]

ENABLE_RESTRICT_WRITER_MIDDLEWARE = get_bool_from_env(
    "ENABLE_RESTRICT_WRITER_MIDDLEWARE", False
)
if ENABLE_RESTRICT_WRITER_MIDDLEWARE:
    MIDDLEWARE = ["saleor.core.db.connection.log_writer_usage_middleware"] + MIDDLEWARE

INSTALLED_APPS = [
    # External apps that need to go before django's
    "storages",
    # Django modules
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django_celery_beat",
    # Local apps
    "saleor.permission",
    "saleor.auth",
    "saleor.plugins",
    "saleor.account",
    "saleor.discount",
    "saleor.giftcard",
    "saleor.product",
    "saleor.attribute",
    "saleor.channel",
    "saleor.checkout",
    "saleor.core",
    "saleor.csv",
    "saleor.graphql",
    "saleor.menu",
    "saleor.order",
    "saleor.invoice",
    "saleor.seo",
    "saleor.shipping",
    "saleor.site",
    "saleor.page",
    "saleor.payment",
    "saleor.tax",
    "saleor.warehouse",
    "saleor.webhook",
    "saleor.app",
    "saleor.thumbnail",
    "saleor.schedulers",
    # External apps
    "django_measurement",
    "django_prices",
    "mptt",
    "django_countries",
    "django_filters",
    "phonenumber_field",
]

ENABLE_DJANGO_EXTENSIONS = get_bool_from_env("ENABLE_DJANGO_EXTENSIONS", False)
if ENABLE_DJANGO_EXTENSIONS:
    INSTALLED_APPS += [
        "django_extensions",
    ]

ENABLE_DEBUG_TOOLBAR = get_bool_from_env("ENABLE_DEBUG_TOOLBAR", False)
if ENABLE_DEBUG_TOOLBAR:
    # Ensure the graphiql debug toolbar is actually installed before adding it
    try:
        __import__("graphiql_debug_toolbar")
    except ImportError as exc:
        msg = (
            f"{exc} -- Install the missing dependencies by "
            f"running `poetry install --no-root`"
        )
        warnings.warn(msg)
    else:
        INSTALLED_APPS += ["django.forms", "debug_toolbar", "graphiql_debug_toolbar"]
        MIDDLEWARE.append("saleor.graphql.middleware.DebugToolbarMiddleware")

        DEBUG_TOOLBAR_PANELS = [
            "ddt_request_history.panels.request_history.RequestHistoryPanel",
            "debug_toolbar.panels.timer.TimerPanel",
            "debug_toolbar.panels.headers.HeadersPanel",
            "debug_toolbar.panels.request.RequestPanel",
            "debug_toolbar.panels.sql.SQLPanel",
            "debug_toolbar.panels.profiling.ProfilingPanel",
        ]
        DEBUG_TOOLBAR_CONFIG = {"RESULTS_CACHE_SIZE": 100}

# Make the `logging` Python module capture `warnings.warn()` calls
# This is needed in order to log them as JSON when DEBUG=False
logging.captureWarnings(True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "INFO", "handlers": ["default"]},
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        },
        "json": {
            "()": "saleor.core.logging.JsonFormatter",
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            "format": (
                "%(asctime)s %(levelname)s %(lineno)s %(message)s %(name)s "
                + "%(pathname)s %(process)d %(threadName)s"
            ),
        },
        "celery_json": {
            "()": "saleor.core.logging.JsonCeleryFormatter",
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            "format": (
                "%(asctime)s %(levelname)s %(celeryTaskId)s %(celeryTaskName)s "
            ),
        },
        "celery_task_json": {
            "()": "saleor.core.logging.JsonCeleryTaskFormatter",
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            "format": (
                "%(asctime)s %(levelname)s %(celeryTaskId)s %(celeryTaskName)s "
                "%(message)s "
            ),
        },
        "verbose": {
            "format": (
                "%(asctime)s %(levelname)s %(name)s %(message)s "
                "[PID:%(process)d:%(threadName)s]"
            )
        },
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "json",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server" if DEBUG else "json",
        },
        "celery_app": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "celery_json",
        },
        "celery_task": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "celery_task_json",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django": {"level": "INFO", "propagate": True},
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.app.trace": {
            "handlers": ["celery_app"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.task": {
            "handlers": ["celery_task"],
            "level": "INFO",
            "propagate": False,
        },
        "saleor": {"level": "DEBUG", "propagate": True},
        "saleor.graphql.errors.handled": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "graphql.execution.utils": {"propagate": False, "handlers": ["null"]},
        "graphql.execution.executor": {"propagate": False, "handlers": ["null"]},
    },
}

AUTH_USER_MODEL = "account.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    }
]

DEFAULT_COUNTRY = os.environ.get("DEFAULT_COUNTRY", "US")
DEFAULT_DECIMAL_PLACES = 3
DEFAULT_MAX_DIGITS = 12
DEFAULT_CURRENCY_CODE_LENGTH = 3

# The default max length for the display name of the
# sender email address.
# Following the recommendation of https://tools.ietf.org/html/rfc5322#section-2.1.1
DEFAULT_MAX_EMAIL_DISPLAY_NAME_LENGTH = 78

COUNTRIES_OVERRIDE = {"EU": "European Union"}

MAX_USER_ADDRESSES = int(os.environ.get("MAX_USER_ADDRESSES", 100))

TEST_RUNNER = "saleor.tests.runner.PytestTestRunner"


PLAYGROUND_ENABLED = get_bool_from_env("PLAYGROUND_ENABLED", True)

ALLOWED_HOSTS = get_list(os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1"))
ALLOWED_GRAPHQL_ORIGINS: list[str] = get_list(
    os.environ.get("ALLOWED_GRAPHQL_ORIGINS", "*")
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Amazon S3 configuration
# See https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_LOCATION = os.environ.get("AWS_LOCATION", "")
AWS_MEDIA_BUCKET_NAME = os.environ.get("AWS_MEDIA_BUCKET_NAME")
AWS_MEDIA_CUSTOM_DOMAIN = os.environ.get("AWS_MEDIA_CUSTOM_DOMAIN")
AWS_QUERYSTRING_AUTH = get_bool_from_env("AWS_QUERYSTRING_AUTH", False)
AWS_QUERYSTRING_EXPIRE = get_bool_from_env("AWS_QUERYSTRING_EXPIRE", 3600)
AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_STATIC_CUSTOM_DOMAIN")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", None)
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", None)
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_DEFAULT_ACL = os.environ.get("AWS_DEFAULT_ACL", None)
AWS_S3_FILE_OVERWRITE = get_bool_from_env("AWS_S3_FILE_OVERWRITE", True)

# Google Cloud Storage configuration
# See https://django-storages.readthedocs.io/en/latest/backends/gcloud.html
GS_PROJECT_ID = os.environ.get("GS_PROJECT_ID")
GS_BUCKET_NAME = os.environ.get("GS_BUCKET_NAME")
GS_LOCATION = os.environ.get("GS_LOCATION", "")
GS_CUSTOM_ENDPOINT = os.environ.get("GS_CUSTOM_ENDPOINT")
GS_MEDIA_BUCKET_NAME = os.environ.get("GS_MEDIA_BUCKET_NAME")
GS_AUTO_CREATE_BUCKET = get_bool_from_env("GS_AUTO_CREATE_BUCKET", False)
GS_QUERYSTRING_AUTH = get_bool_from_env("GS_QUERYSTRING_AUTH", False)
GS_DEFAULT_ACL = os.environ.get("GS_DEFAULT_ACL", None)
GS_MEDIA_CUSTOM_ENDPOINT = os.environ.get("GS_MEDIA_CUSTOM_ENDPOINT", None)
GS_EXPIRATION = timedelta(seconds=parse(os.environ.get("GS_EXPIRATION", "1 day")))
GS_FILE_OVERWRITE = get_bool_from_env("GS_FILE_OVERWRITE", True)

# If GOOGLE_APPLICATION_CREDENTIALS is set there is no need to load OAuth token
# See https://django-storages.readthedocs.io/en/latest/backends/gcloud.html
if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
    GS_CREDENTIALS = os.environ.get("GS_CREDENTIALS")

# Azure Storage configuration
# See https://django-storages.readthedocs.io/en/latest/backends/azure.html
AZURE_ACCOUNT_NAME = os.environ.get("AZURE_ACCOUNT_NAME")
AZURE_ACCOUNT_KEY = os.environ.get("AZURE_ACCOUNT_KEY")
AZURE_CONTAINER = os.environ.get("AZURE_CONTAINER")
AZURE_SSL = os.environ.get("AZURE_SSL")

if AWS_STORAGE_BUCKET_NAME:
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
elif GS_BUCKET_NAME:
    STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"

if AWS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "saleor.core.storages.S3MediaStorage"
elif GS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "saleor.core.storages.GCSMediaStorage"
elif AZURE_CONTAINER:
    DEFAULT_FILE_STORAGE = "saleor.core.storages.AzureMediaStorage"

PLACEHOLDER_IMAGES = {
    32: "images/placeholder32.png",
    64: "images/placeholder64.png",
    128: "images/placeholder128.png",
    256: "images/placeholder256.png",
    512: "images/placeholder512.png",
    1024: "images/placeholder1024.png",
    2048: "images/placeholder2048.png",
    4096: "images/placeholder4096.png",
}


AUTHENTICATION_BACKENDS = [
    "saleor.core.auth_backend.JSONWebTokenBackend",
    "saleor.core.auth_backend.PluginBackend",
]

# Expired checkouts settings - defines after what time checkouts will be deleted
ANONYMOUS_CHECKOUTS_TIMEDELTA = timedelta(
    seconds=parse(os.environ.get("ANONYMOUS_CHECKOUTS_TIMEDELTA", "30 days"))
)
USER_CHECKOUTS_TIMEDELTA = timedelta(
    seconds=parse(os.environ.get("USER_CHECKOUTS_TIMEDELTA", "90 days"))
)
EMPTY_CHECKOUTS_TIMEDELTA = timedelta(
    seconds=parse(os.environ.get("EMPTY_CHECKOUTS_TIMEDELTA", "6 hours"))
)

# Exports settings - defines after what time exported files will be deleted
EXPORT_FILES_TIMEDELTA = timedelta(
    seconds=parse(os.environ.get("EXPORT_FILES_TIMEDELTA", "30 days"))
)

# CELERY SETTINGS
CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_URL = (
    os.environ.get("CELERY_BROKER_URL", os.environ.get("CLOUDAMQP_URL")) or ""
)
CELERY_TASK_ALWAYS_EAGER = not CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", None)

# Expire orders task setting
BEAT_EXPIRE_ORDERS_AFTER_TIMEDELTA = timedelta(
    seconds=parse(os.environ.get("BEAT_EXPIRE_ORDERS_AFTER_TIMEDELTA", "5 minutes"))
)

# Defines after how many seconds should the task triggered by the Celery beat
# entry 'update-products-search-vectors' expire if it wasn't picked up by a worker.
BEAT_UPDATE_SEARCH_SEC = parse(
    os.environ.get("BEAT_UPDATE_SEARCH_FREQUENCY", "20 seconds")
)
BEAT_UPDATE_SEARCH_EXPIRE_AFTER_SEC = BEAT_UPDATE_SEARCH_SEC

BEAT_PRICE_RECALCULATION_SCHEDULE = parse(
    os.environ.get("BEAT_PRICE_RECALCULATION_SCHEDULE", "30 seconds")
)
BEAT_PRICE_RECALCULATION_SCHEDULE_EXPIRE_AFTER_SEC = BEAT_PRICE_RECALCULATION_SCHEDULE

# Defines the Celery beat scheduler entries.
#
# Note: if a Celery task triggered by a Celery beat entry has an expiration
# @task(expires=...), the Celery beat scheduler entry should also define
# the expiration value. This makes sure if the task or scheduling is wrapped
# by custom code (e.g., a Saleor fork), the expiration is still present.
CELERY_BEAT_SCHEDULE = {
    "delete-empty-allocations": {
        "task": "saleor.warehouse.tasks.delete_empty_allocations_task",
        "schedule": timedelta(days=1),
    },
    "deactivate-preorder-for-variants": {
        "task": "saleor.product.tasks.deactivate_preorder_for_variants_task",
        "schedule": timedelta(hours=1),
    },
    "delete-expired-reservations": {
        "task": "saleor.warehouse.tasks.delete_expired_reservations_task",
        "schedule": timedelta(days=1),
    },
    "delete-expired-checkouts": {
        "task": "saleor.checkout.tasks.delete_expired_checkouts",
        "schedule": crontab(hour=0, minute=0),
    },
    "delete_expired_orders": {
        "task": "saleor.order.tasks.delete_expired_orders_task",
        "schedule": crontab(hour=2, minute=0),
    },
    "delete-outdated-event-data": {
        "task": "saleor.core.tasks.delete_event_payloads_task",
        "schedule": timedelta(days=1),
    },
    "deactivate-expired-gift-cards": {
        "task": "saleor.giftcard.tasks.deactivate_expired_cards_task",
        "schedule": crontab(hour=0, minute=0),
    },
    "update-stocks-quantity-allocated": {
        "task": "saleor.warehouse.tasks.update_stocks_quantity_allocated_task",
        "schedule": crontab(hour=0, minute=0),
    },
    "delete-old-export-files": {
        "task": "saleor.csv.tasks.delete_old_export_files",
        "schedule": crontab(hour=1, minute=0),
    },
    "handle-promotion-toggle": {
        "task": "saleor.discount.tasks.handle_promotion_toggle",
        "schedule": initiated_promotion_webhook_schedule,
    },
    "update-products-search-vectors": {
        "task": "saleor.product.tasks.update_products_search_vector_task",
        "schedule": timedelta(seconds=BEAT_UPDATE_SEARCH_SEC),
        "options": {"expires": BEAT_UPDATE_SEARCH_EXPIRE_AFTER_SEC},
    },
    "update-gift-cards-search-vectors": {
        "task": "saleor.giftcard.tasks.update_gift_cards_search_vector_task",
        "schedule": timedelta(seconds=BEAT_UPDATE_SEARCH_SEC),
        "options": {"expires": BEAT_UPDATE_SEARCH_EXPIRE_AFTER_SEC},
    },
    "expire-orders": {
        "task": "saleor.order.tasks.expire_orders_task",
        "schedule": BEAT_EXPIRE_ORDERS_AFTER_TIMEDELTA,
    },
    "remove-apps-marked-as-removed": {
        "task": "saleor.app.tasks.remove_apps_task",
        "schedule": crontab(hour=3, minute=0),
    },
    "release-funds-for-abandoned-checkouts": {
        "task": "saleor.payment.tasks.transaction_release_funds_for_checkout_task",
        "schedule": timedelta(minutes=10),
    },
    "recalculate-promotion-rules": {
        "task": (
            "saleor.product.tasks"
            ".update_variant_relations_for_active_promotion_rules_task"
        ),
        "schedule": timedelta(seconds=BEAT_PRICE_RECALCULATION_SCHEDULE),
        "options": {"expires": BEAT_PRICE_RECALCULATION_SCHEDULE_EXPIRE_AFTER_SEC},
    },
    "recalculate-discounted-price-for-products": {
        "task": "saleor.product.tasks.recalculate_discounted_price_for_products_task",
        "schedule": timedelta(seconds=BEAT_PRICE_RECALCULATION_SCHEDULE),
        "options": {"expires": BEAT_PRICE_RECALCULATION_SCHEDULE_EXPIRE_AFTER_SEC},
    },
}

# The maximum wait time between each is_due() call on schedulers
# It needs to be higher than the frequency of the schedulers to avoid unnecessary
# is_due() calls
CELERY_BEAT_MAX_LOOP_INTERVAL = 300  # 5 minutes

EVENT_PAYLOAD_DELETE_PERIOD = timedelta(
    seconds=parse(os.environ.get("EVENT_PAYLOAD_DELETE_PERIOD", "14 days"))
)
EVENT_PAYLOAD_DELETE_TASK_TIME_LIMIT = timedelta(
    seconds=parse(os.environ.get("EVENT_PAYLOAD_DELETE_TASK_TIME_LIMIT", "1 hour"))
)
# Time between marking app "to remove" and removing the app from the database.
# App is not visible for the user after removing, but it still exists in the database.
# Saleor needs time to process sending `APP_DELETED` webhook and possible retrying,
# so we need to wait for some time before removing the App from the database.
DELETE_APP_TTL = timedelta(seconds=parse(os.environ.get("DELETE_APP_TTL", "1 day")))


# Observability settings
OBSERVABILITY_BROKER_URL = os.environ.get("OBSERVABILITY_BROKER_URL")
OBSERVABILITY_ACTIVE = bool(OBSERVABILITY_BROKER_URL)
OBSERVABILITY_REPORT_ALL_API_CALLS = get_bool_from_env(
    "OBSERVABILITY_REPORT_ALL_API_CALLS", False
)
OBSERVABILITY_MAX_PAYLOAD_SIZE = int(
    os.environ.get("OBSERVABILITY_MAX_PAYLOAD_SIZE", 25 * 1000)
)
OBSERVABILITY_BUFFER_SIZE_LIMIT = int(
    os.environ.get("OBSERVABILITY_BUFFER_SIZE_LIMIT", 1000)
)
OBSERVABILITY_BUFFER_BATCH_SIZE = int(
    os.environ.get("OBSERVABILITY_BUFFER_BATCH_SIZE", 100)
)
OBSERVABILITY_REPORT_PERIOD = timedelta(
    seconds=parse(os.environ.get("OBSERVABILITY_REPORT_PERIOD", "20 seconds"))
)
OBSERVABILITY_BUFFER_TIMEOUT = timedelta(
    seconds=parse(os.environ.get("OBSERVABILITY_BUFFER_TIMEOUT", "5 minutes"))
)
if OBSERVABILITY_ACTIVE:
    CELERY_BEAT_SCHEDULE["observability-reporter"] = {
        "task": "saleor.webhook.transport.asynchronous.transport.observability_reporter_task",  # noqa
        "schedule": OBSERVABILITY_REPORT_PERIOD,
        "options": {"expires": OBSERVABILITY_REPORT_PERIOD.total_seconds()},
    }
    if OBSERVABILITY_BUFFER_TIMEOUT < OBSERVABILITY_REPORT_PERIOD * 2:
        warnings.warn(
            "OBSERVABILITY_REPORT_PERIOD is too big compared to "
            "OBSERVABILITY_BUFFER_TIMEOUT. That can lead to a loss of events."
        )

# Change this value if your application is running behind a proxy,
# e.g. HTTP_CF_Connecting_IP for Cloudflare or X_FORWARDED_FOR
REAL_IP_ENVIRON = get_list(os.environ.get("REAL_IP_ENVIRON", "REMOTE_ADDR"))

# Slugs for menus precreated in Django migrations
DEFAULT_MENUS = {"top_menu_name": "navbar", "bottom_menu_name": "footer"}

# Slug for channel precreated in Django migrations
DEFAULT_CHANNEL_SLUG = os.environ.get("DEFAULT_CHANNEL_SLUG", "default-channel")

# Set this to `True` if you want to create default channel, warehouse, product type and
# category during migrations. It makes it easier for the users to create their first
# product.
POPULATE_DEFAULTS = get_bool_from_env("POPULATE_DEFAULTS", True)


#  Sentry
sentry_sdk.utils.MAX_STRING_LENGTH = 4096  # type: ignore[attr-defined]
SENTRY_DSN = os.environ.get("SENTRY_DSN")
SENTRY_OPTS = {"integrations": [CeleryIntegration(), DjangoIntegration()]}


def SENTRY_INIT(dsn: str, sentry_opts: dict):
    """Init function for sentry.

    Will only be called if SENTRY_DSN is not None, during core start, can be
    overriden in separate settings file.
    """
    sentry_sdk.init(dsn, release=__version__, **sentry_opts)
    ignore_logger("graphql.execution.utils")
    ignore_logger("graphql.execution.executor")


GRAPHQL_PAGINATION_LIMIT = 100
GRAPHQL_MIDDLEWARE: list[str] = []

# Set GRAPHQL_QUERY_MAX_COMPLEXITY=0 in env to disable (not recommended)
GRAPHQL_QUERY_MAX_COMPLEXITY = int(
    os.environ.get("GRAPHQL_QUERY_MAX_COMPLEXITY", 50000)
)

# Max number entities that can be requested in single query by Apollo Federation
# Federation protocol implements no securities on its own part - malicious actor
# may build a query that requests for potentially few thousands of entities.
# Set FEDERATED_QUERY_MAX_ENTITIES=0 in env to disable (not recommended)
FEDERATED_QUERY_MAX_ENTITIES = int(os.environ.get("FEDERATED_QUERY_MAX_ENTITIES", 100))

BUILTIN_PLUGINS = [
    "saleor.plugins.avatax.plugin.AvataxPlugin",
    "saleor.plugins.webhook.plugin.WebhookPlugin",
    "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin",
    "saleor.payment.gateways.dummy_credit_card.plugin.DummyCreditCardGatewayPlugin",
    "saleor.payment.gateways.stripe.deprecated.plugin.DeprecatedStripeGatewayPlugin",
    "saleor.payment.gateways.stripe.plugin.StripeGatewayPlugin",
    "saleor.payment.gateways.braintree.plugin.BraintreeGatewayPlugin",
    "saleor.payment.gateways.razorpay.plugin.RazorpayGatewayPlugin",
    "saleor.payment.gateways.adyen.plugin.AdyenGatewayPlugin",
    "saleor.payment.gateways.authorize_net.plugin.AuthorizeNetGatewayPlugin",
    "saleor.payment.gateways.np_atobarai.plugin.NPAtobaraiGatewayPlugin",
    "saleor.plugins.invoicing.plugin.InvoicingPlugin",
    "saleor.plugins.user_email.plugin.UserEmailPlugin",
    "saleor.plugins.admin_email.plugin.AdminEmailPlugin",
    "saleor.plugins.sendgrid.plugin.SendgridEmailPlugin",
    "saleor.plugins.openid_connect.plugin.OpenIDConnectPlugin",
]

# Plugin discovery
EXTERNAL_PLUGINS = []
installed_plugins = pkg_resources.iter_entry_points("saleor.plugins")
for entry_point in installed_plugins:
    plugin_path = f"{entry_point.module_name}.{entry_point.attrs[0]}"
    if plugin_path not in BUILTIN_PLUGINS and plugin_path not in EXTERNAL_PLUGINS:
        if entry_point.name not in INSTALLED_APPS:
            INSTALLED_APPS.append(entry_point.name)
        EXTERNAL_PLUGINS.append(plugin_path)

PLUGINS = BUILTIN_PLUGINS + EXTERNAL_PLUGINS

# When `True`, HTTP requests made from arbitrary URLs will be rejected (e.g., webhooks).
# if they try to access private IP address ranges, and loopback ranges (unless
# `HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS=False`).
HTTP_IP_FILTER_ENABLED: bool = get_bool_from_env("HTTP_IP_FILTER_ENABLED", True)

# When `False` it rejects loopback IPs during external calls.
# Refer to `HTTP_IP_FILTER_ENABLED` for more details.
HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS: bool = get_bool_from_env(
    "HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS", False
)

# Since we split checkout complete logic into two separate transactions, in order to
# mimic stock lock, we apply short reservation for the stocks. The value represents
# time of the reservation in seconds.
RESERVE_DURATION = 45

# Initialize a simple and basic Jaeger Tracing integration
# for open-tracing if enabled.
#
# Refer to our guide on https://docs.saleor.io/docs/next/guides/opentracing-jaeger/.
#
# If running locally, set:
#   JAEGER_AGENT_HOST=localhost
JAEGER_HOST = os.environ.get("JAEGER_AGENT_HOST")
if JAEGER_HOST:
    jaeger_client.Config(
        config={
            "sampler": {"type": "const", "param": 1},
            "local_agent": {
                "reporting_port": os.environ.get(
                    "JAEGER_AGENT_PORT", jaeger_client.config.DEFAULT_REPORTING_PORT
                ),
                "reporting_host": JAEGER_HOST,
            },
            "logging": get_bool_from_env("JAEGER_LOGGING", False),
        },
        service_name="saleor",
        validate=True,
    ).initialize_tracer()


# Some cloud providers (Heroku) export REDIS_URL variable instead of CACHE_URL
REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    CACHE_URL = os.environ.setdefault("CACHE_URL", REDIS_URL)
CACHES = {"default": django_cache_url.config()}
CACHES["default"]["TIMEOUT"] = parse(os.environ.get("CACHE_TIMEOUT", "7 days"))

JWT_EXPIRE = True
JWT_TTL_ACCESS = timedelta(seconds=parse(os.environ.get("JWT_TTL_ACCESS", "5 minutes")))
JWT_TTL_APP_ACCESS = timedelta(
    seconds=parse(os.environ.get("JWT_TTL_APP_ACCESS", "5 minutes"))
)
JWT_TTL_REFRESH = timedelta(seconds=parse(os.environ.get("JWT_TTL_REFRESH", "30 days")))


JWT_TTL_REQUEST_EMAIL_CHANGE = timedelta(
    seconds=parse(os.environ.get("JWT_TTL_REQUEST_EMAIL_CHANGE", "1 hour")),
)

CHECKOUT_PRICES_TTL = timedelta(
    seconds=parse(os.environ.get("CHECKOUT_PRICES_TTL", "1 hour"))
)

CHECKOUT_TTL_BEFORE_RELEASING_FUNDS = timedelta(
    seconds=parse(os.environ.get("CHECKOUT_TTL_BEFORE_RELEASING_FUNDS", "6 hours"))
)
CHECKOUT_BATCH_FOR_RELEASING_FUNDS = os.environ.get(
    "CHECKOUT_BATCH_FOR_RELEASING_FUNDS", 30
)
TRANSACTION_BATCH_FOR_RELEASING_FUNDS = os.environ.get(
    "TRANSACTION_BATCH_FOR_RELEASING_FUNDS", 60
)


# The maximum SearchVector expression count allowed per index SQL statement
# If the count is exceeded, the expression list will be truncated
INDEX_MAXIMUM_EXPR_COUNT = 4000

# Maximum related objects that can be indexed in an order
SEARCH_ORDERS_MAX_INDEXED_TRANSACTIONS = 20
SEARCH_ORDERS_MAX_INDEXED_PAYMENTS = 20
SEARCH_ORDERS_MAX_INDEXED_DISCOUNTS = 20
SEARCH_ORDERS_MAX_INDEXED_LINES = 100

# Maximum related objects that can be indexed in a product
PRODUCT_MAX_INDEXED_ATTRIBUTES = 1000
PRODUCT_MAX_INDEXED_ATTRIBUTE_VALUES = 100
PRODUCT_MAX_INDEXED_VARIANTS = 1000


# Patch SubscriberExecutionContext class from `graphql-core-legacy` package
# to fix bug causing not returning errors for subscription queries.

executor.SubscriberExecutionContext = PatchedSubscriberExecutionContext  # type: ignore

patch_executor()

# Optional queue names for Celery tasks.
# Set None to route to the default queue, or a string value to use a separate one
#
# Queue name for update search vector
UPDATE_SEARCH_VECTOR_INDEX_QUEUE_NAME = os.environ.get(
    "UPDATE_SEARCH_VECTOR_INDEX_QUEUE_NAME", None
)
# Queue name for "async webhook" events
WEBHOOK_CELERY_QUEUE_NAME = os.environ.get("WEBHOOK_CELERY_QUEUE_NAME", None)
CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME = os.environ.get(
    "CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME", WEBHOOK_CELERY_QUEUE_NAME
)
ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME = os.environ.get(
    "ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME", WEBHOOK_CELERY_QUEUE_NAME
)


# Queue name for execution of collection product_updated events
COLLECTION_PRODUCT_UPDATED_QUEUE_NAME = os.environ.get(
    "COLLECTION_PRODUCT_UPDATED_QUEUE_NAME", None
)

# Lock time for request password reset mutation per user (seconds)
RESET_PASSWORD_LOCK_TIME = parse(
    os.environ.get("RESET_PASSWORD_LOCK_TIME", "15 minutes")
)

# Lock time for request confirmation email mutation per user
CONFIRMATION_EMAIL_LOCK_TIME = parse(
    os.environ.get("CONFIRMATION_EMAIL_LOCK_TIME", "15 minutes")
)

# Time threshold to update user last_login when performing requests with OAUTH token.
OAUTH_UPDATE_LAST_LOGIN_THRESHOLD = parse(
    os.environ.get("OAUTH_UPDATE_LAST_LOGIN_THRESHOLD", "15 minutes")
)

# Time threshold to update user last_login when using tokenCreate/tokenRefresh
# mutations.
TOKEN_UPDATE_LAST_LOGIN_THRESHOLD = parse(
    os.environ.get("TOKEN_UPDATE_LAST_LOGIN_THRESHOLD", "5 seconds")
)

# Max lock time for checkout processing.
# It prevents locking checkout when unhandled issue appears.
CHECKOUT_COMPLETION_LOCK_TIME = parse(
    os.environ.get("CHECKOUT_COMPLETION_LOCK_TIME", "3 minutes")
)

# Default timeout (sec) for establishing a connection when performing external requests.
REQUESTS_CONN_EST_TIMEOUT = 2

# Default timeout for external requests.
COMMON_REQUESTS_TIMEOUT = (REQUESTS_CONN_EST_TIMEOUT, 18)

WEBHOOK_TIMEOUT = (REQUESTS_CONN_EST_TIMEOUT, 18)
WEBHOOK_SYNC_TIMEOUT = (REQUESTS_CONN_EST_TIMEOUT, 18)

# The max number of rules with order_predicate defined
ORDER_RULES_LIMIT = os.environ.get("ORDER_RULES_LIMIT", 100)

# The max number of gits assigned to promotion rule
GIFTS_LIMIT_PER_RULE = os.environ.get("GIFTS_LIMIT_PER_RULE", 500)

# Whether to enable the comparison of pre-save and post-save webhook payloads in
# mutations, in order to limit sending webhooks where the payload has not changed as
# a result of the mutation. Note: this works only for subscriptions webhooks; legacy
# payloads are not supported.
ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS = get_bool_from_env(
    "ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS", False
)


# Transaction items limit for PaymentGatewayInitialize / TransactionInitialize.
# That setting limits the allowed number of transaction items for single entity.
TRANSACTION_ITEMS_LIMIT = 100
