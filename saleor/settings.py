import ast
import os.path
import warnings
from datetime import timedelta

import dj_database_url
import dj_email_url
import django_cache_url
import jaeger_client.config
import pkg_resources
import sentry_sdk
import sentry_sdk.utils
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from graphql.execution import executor
from pytimeparse import parse
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger

from . import PatchedSubscriberExecutionContext, __version__
from .core.languages import LANGUAGES as CORE_LANGUAGES
from .core.schedules import initiated_sale_webhook_schedule


def get_list(text):
    return [item.strip() for item in text.split(",")]


def get_bool_from_env(name, default_value):
    if name in os.environ:
        value = os.environ[name]
        try:
            return ast.literal_eval(value)
        except ValueError as e:
            raise ValueError("{} is an invalid value for {}".format(value, name)) from e
    return default_value


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

DATABASE_CONNECTION_DEFAULT_NAME = "default"
# TODO: For local envs will be activated in separate PR.
# We need to update docs an saleor platform.
# This variable should be set to `replica`
DATABASE_CONNECTION_REPLICA_NAME = "default"

DATABASES = {
    DATABASE_CONNECTION_DEFAULT_NAME: dj_database_url.config(
        default="postgres://saleor:saleor@localhost:5432/saleor", conn_max_age=600
    ),
    # TODO: We need to add read only user to saleor platfrom, and we need to update
    # docs.
    # DATABASE_CONNECTION_REPLICA_NAME: dj_database_url.config(
    #     default="postgres://saleor_read_only:saleor@localhost:5432/saleor",
    #     conn_max_age=600,
    # ),
}

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
    EMAIL_URL = "smtp://%s:%s@smtp.sendgrid.net:587/?tls=True" % (
        SENDGRID_USERNAME,
        SENDGRID_PASSWORD,
    )
email_config = dj_email_url.parse(
    EMAIL_URL or "console://demo@example.com:console@example/"
)

EMAIL_FILE_PATH = email_config["EMAIL_FILE_PATH"]
EMAIL_HOST_USER = email_config["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = email_config["EMAIL_HOST_PASSWORD"]
EMAIL_HOST = email_config["EMAIL_HOST"]
EMAIL_PORT = email_config["EMAIL_PORT"]
EMAIL_BACKEND = email_config["EMAIL_BACKEND"]
EMAIL_USE_TLS = email_config["EMAIL_USE_TLS"]
EMAIL_USE_SSL = email_config["EMAIL_USE_SSL"]

# If enabled, make sure you have set proper storefront address in ALLOWED_CLIENT_HOSTS.
ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL = get_bool_from_env(
    "ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL", True
)

ENABLE_SSL = get_bool_from_env("ENABLE_SSL", False)

if ENABLE_SSL:
    SECURE_SSL_REDIRECT = not DEBUG

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")
MEDIA_URL = os.environ.get("MEDIA_URL", "/media/")

STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")
STATIC_URL = os.environ.get("STATIC_URL", "/static/")
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
    "saleor.core.middleware.request_time",
    "saleor.core.middleware.discounts",
    "saleor.core.middleware.google_analytics",
    "saleor.core.middleware.site",
    "saleor.core.middleware.plugins",
    "saleor.core.middleware.jwt_refresh_token_middleware",
]

INSTALLED_APPS = [
    # External apps that need to go before django's
    "storages",
    # Django modules
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.auth",
    "django.contrib.postgres",
    "django_celery_beat",
    # Local apps
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
    "saleor.warehouse",
    "saleor.webhook",
    "saleor.app",
    "saleor.thumbnail",
    "saleor.schedulers",
    # External apps
    "django_measurement",
    "django_prices",
    "django_prices_openexchangerates",
    "django_prices_vatlayer",
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
            f"running `pip install -r requirements_dev.txt`"
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

OPENEXCHANGERATES_API_KEY = os.environ.get("OPENEXCHANGERATES_API_KEY")

GOOGLE_ANALYTICS_TRACKING_ID = os.environ.get("GOOGLE_ANALYTICS_TRACKING_ID")


def get_host():
    from django.contrib.sites.models import Site

    return Site.objects.get_current().domain


PAYMENT_HOST = get_host

PAYMENT_MODEL = "order.Payment"

MAX_USER_ADDRESSES = int(os.environ.get("MAX_USER_ADDRESSES", 100))

TEST_RUNNER = "saleor.tests.runner.PytestTestRunner"


PLAYGROUND_ENABLED = get_bool_from_env("PLAYGROUND_ENABLED", True)

ALLOWED_HOSTS = get_list(os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1"))
ALLOWED_GRAPHQL_ORIGINS = get_list(os.environ.get("ALLOWED_GRAPHQL_ORIGINS", "*"))

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
GS_PROJECT_ID = os.environ.get("GS_PROJECT_ID")
GS_BUCKET_NAME = os.environ.get("GS_BUCKET_NAME")
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
CELERY_TASK_ROUTES = {
    "saleor.plugins.webhook.tasks.observability_reporter_task": {
        "queue": "observability"
    },
    "saleor.plugins.webhook.tasks.observability_send_events": {
        "queue": "observability"
    },
}

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
    "send-sale-toggle-notifications": {
        "task": "saleor.discount.tasks.send_sale_toggle_notifications",
        "schedule": initiated_sale_webhook_schedule,
    },
    "update-products-search-vectors": {
        "task": "saleor.product.tasks.update_products_search_vector_task",
        "schedule": timedelta(seconds=20),
    },
}

# The maximum wait time between each is_due() call on schedulers
# It needs to be higher than the frequency of the schedulers to avoid unnecessary
# is_due() calls
CELERY_BEAT_MAX_LOOP_INTERVAL = 300  # 5 minutes

EVENT_PAYLOAD_DELETE_PERIOD = timedelta(
    seconds=parse(os.environ.get("EVENT_PAYLOAD_DELETE_PERIOD", "14 days"))
)

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
        "task": "saleor.plugins.webhook.tasks.observability_reporter_task",
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
REAL_IP_ENVIRON = os.environ.get("REAL_IP_ENVIRON", "REMOTE_ADDR")

# Slugs for menus precreated in Django migrations
DEFAULT_MENUS = {"top_menu_name": "navbar", "bottom_menu_name": "footer"}

# Slug for channel precreated in Django migrations
DEFAULT_CHANNEL_SLUG = os.environ.get("DEFAULT_CHANNEL_SLUG", "default-channel")

# Set this to `True` if you want to create default channel, warehouse, product type and
# category during migrations. It makes it easier for the users to create their first
# product.
POPULATE_DEFAULTS = get_bool_from_env("POPULATE_DEFAULTS", True)


#  Sentry
sentry_sdk.utils.MAX_STRING_LENGTH = 4096
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


GRAPHENE = {
    "RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST": True,
    "RELAY_CONNECTION_MAX_LIMIT": 100,
}

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
    "saleor.plugins.vatlayer.plugin.VatlayerPlugin",
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
    plugin_path = "{}.{}".format(entry_point.module_name, entry_point.attrs[0])
    if plugin_path not in BUILTIN_PLUGINS and plugin_path not in EXTERNAL_PLUGINS:
        if entry_point.name not in INSTALLED_APPS:
            INSTALLED_APPS.append(entry_point.name)
        EXTERNAL_PLUGINS.append(plugin_path)

PLUGINS = BUILTIN_PLUGINS + EXTERNAL_PLUGINS

if (
    not DEBUG
    and ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL
    and ALLOWED_CLIENT_HOSTS == get_list(_DEFAULT_CLIENT_HOSTS)
):
    raise ImproperlyConfigured(
        "Make sure you've added storefront address to ALLOWED_CLIENT_HOSTS "
        "if ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL is enabled."
    )

# Timeouts for webhook requests. Sync webhooks (eg. payment webhook) need more time
# for getting response from the server.
WEBHOOK_TIMEOUT = 10
WEBHOOK_SYNC_TIMEOUT = 20

# Initialize a simple and basic Jaeger Tracing integration
# for open-tracing if enabled.
#
# Refer to our guide on https://docs.saleor.io/docs/next/guides/opentracing-jaeger/.
#
# If running locally, set:
#   JAEGER_AGENT_HOST=localhost
if "JAEGER_AGENT_HOST" in os.environ:
    jaeger_client.Config(
        config={
            "sampler": {"type": "const", "param": 1},
            "local_agent": {
                "reporting_port": os.environ.get(
                    "JAEGER_AGENT_PORT", jaeger_client.config.DEFAULT_REPORTING_PORT
                ),
                "reporting_host": os.environ.get("JAEGER_AGENT_HOST"),
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

# The maximum SearchVector expression count allowed per index SQL statement
# If the count is exceeded, the expression list will be truncated
INDEX_MAXIMUM_EXPR_COUNT = 4000

# Maximum related objects that can be indexed in an order
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

UPDATE_SEARCH_VECTOR_INDEX_QUEUE_NAME = os.environ.get(
    "UPDATE_SEARCH_VECTOR_INDEX_QUEUE_NAME", None
)
