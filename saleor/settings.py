import ast
import os.path
import warnings
from datetime import timedelta

import dj_database_url
import dj_email_url
import django_cache_url
import jaeger_client
import jaeger_client.config
import pkg_resources
import sentry_sdk
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from pytimeparse import parse
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration


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

DATABASES = {
    "default": dj_database_url.config(
        default="postgres://saleor:saleor@localhost:5432/saleor", conn_max_age=600
    )
}


TIME_ZONE = "UTC"
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("ar", "Arabic"),
    ("az", "Azerbaijani"),
    ("bg", "Bulgarian"),
    ("bn", "Bengali"),
    ("ca", "Catalan"),
    ("cs", "Czech"),
    ("da", "Danish"),
    ("de", "German"),
    ("el", "Greek"),
    ("en", "English"),
    ("es", "Spanish"),
    ("es-co", "Colombian Spanish"),
    ("et", "Estonian"),
    ("fa", "Persian"),
    ("fi", "Finnish"),
    ("fr", "French"),
    ("hi", "Hindi"),
    ("hu", "Hungarian"),
    ("hy", "Armenian"),
    ("id", "Indonesian"),
    ("is", "Icelandic"),
    ("it", "Italian"),
    ("ja", "Japanese"),
    ("ka", "Georgian"),
    ("km", "Khmer"),
    ("ko", "Korean"),
    ("lt", "Lithuanian"),
    ("mn", "Mongolian"),
    ("my", "Burmese"),
    ("nb", "Norwegian"),
    ("nl", "Dutch"),
    ("pl", "Polish"),
    ("pt", "Portuguese"),
    ("pt-br", "Brazilian Portuguese"),
    ("ro", "Romanian"),
    ("ru", "Russian"),
    ("sk", "Slovak"),
    ("sl", "Slovenian"),
    ("sq", "Albanian"),
    ("sr", "Serbian"),
    ("sv", "Swedish"),
    ("sw", "Swahili"),
    ("ta", "Tamil"),
    ("th", "Thai"),
    ("tr", "Turkish"),
    ("uk", "Ukrainian"),
    ("vi", "Vietnamese"),
    ("zh-hans", "Simplified Chinese"),
    ("zh-hant", "Traditional Chinese"),
]
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

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(PROJECT_ROOT, "templates")],
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

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "saleor.core.middleware.request_time",
    "saleor.core.middleware.discounts",
    "saleor.core.middleware.google_analytics",
    "saleor.core.middleware.country",
    "saleor.core.middleware.currency",
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
    # Local apps
    "saleor.plugins",
    "saleor.account",
    "saleor.discount",
    "saleor.giftcard",
    "saleor.product",
    "saleor.checkout",
    "saleor.core",
    "saleor.csv",
    "saleor.graphql",
    "saleor.menu",
    "saleor.order",
    "saleor.invoice",
    "saleor.seo",
    "saleor.shipping",
    "saleor.search",
    "saleor.site",
    "saleor.data_feeds",
    "saleor.page",
    "saleor.payment",
    "saleor.warehouse",
    "saleor.webhook",
    "saleor.wishlist",
    "saleor.app",
    # External apps
    "versatileimagefield",
    "django_measurement",
    "django_prices",
    "django_prices_openexchangerates",
    "django_prices_vatlayer",
    "graphene_django",
    "mptt",
    "django_countries",
    "django_filters",
    "phonenumber_field",
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
        "verbose": {
            "format": (
                "%(levelname)s %(name)s %(message)s [PID:%(process)d:%(threadName)s]"
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
    },
    "loggers": {
        "django": {"level": "INFO", "propagate": True},
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "saleor": {"level": "DEBUG", "propagate": True},
        "saleor.graphql.errors.handled": {
            "handlers": ["default"],
            "level": "ERROR",
            "propagate": False,
        },
        "graphql.execution.utils": {"propagate": False},
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
DEFAULT_CURRENCY = os.environ.get("DEFAULT_CURRENCY", "USD")
DEFAULT_DECIMAL_PLACES = 3
DEFAULT_MAX_DIGITS = 12
DEFAULT_CURRENCY_CODE_LENGTH = 3

# The default max length for the display name of the
# sender email address.
# Following the recommendation of https://tools.ietf.org/html/rfc5322#section-2.1.1
DEFAULT_MAX_EMAIL_DISPLAY_NAME_LENGTH = 78

# note: having multiple currencies is not supported yet
AVAILABLE_CURRENCIES = [DEFAULT_CURRENCY]

COUNTRIES_OVERRIDE = {"EU": "European Union"}

OPENEXCHANGERATES_API_KEY = os.environ.get("OPENEXCHANGERATES_API_KEY")

GOOGLE_ANALYTICS_TRACKING_ID = os.environ.get("GOOGLE_ANALYTICS_TRACKING_ID")


def get_host():
    from django.contrib.sites.models import Site

    return Site.objects.get_current().domain


PAYMENT_HOST = get_host

PAYMENT_MODEL = "order.Payment"

MAX_CHECKOUT_LINE_QUANTITY = int(os.environ.get("MAX_CHECKOUT_LINE_QUANTITY", 50))

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

# Google Cloud Storage configuration
GS_PROJECT_ID = os.environ.get("GS_PROJECT_ID")
GS_STORAGE_BUCKET_NAME = os.environ.get("GS_STORAGE_BUCKET_NAME")
GS_MEDIA_BUCKET_NAME = os.environ.get("GS_MEDIA_BUCKET_NAME")
GS_AUTO_CREATE_BUCKET = get_bool_from_env("GS_AUTO_CREATE_BUCKET", False)

# If GOOGLE_APPLICATION_CREDENTIALS is set there is no need to load OAuth token
# See https://django-storages.readthedocs.io/en/latest/backends/gcloud.html
if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
    GS_CREDENTIALS = os.environ.get("GS_CREDENTIALS")

if AWS_STORAGE_BUCKET_NAME:
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
elif GS_STORAGE_BUCKET_NAME:
    STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"

if AWS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "saleor.core.storages.S3MediaStorage"
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE
elif GS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "saleor.core.storages.GCSMediaStorage"
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    "products": [
        ("product_gallery", "thumbnail__540x540"),
        ("product_gallery_2x", "thumbnail__1080x1080"),
        ("product_small", "thumbnail__60x60"),
        ("product_small_2x", "thumbnail__120x120"),
        ("product_list", "thumbnail__255x255"),
        ("product_list_2x", "thumbnail__510x510"),
    ],
    "background_images": [("header_image", "thumbnail__1080x440")],
    "user_avatars": [("default", "thumbnail__445x445")],
}

VERSATILEIMAGEFIELD_SETTINGS = {
    # Images should be pre-generated on Production environment
    "create_images_on_demand": get_bool_from_env("CREATE_IMAGES_ON_DEMAND", DEBUG)
}

PLACEHOLDER_IMAGES = {
    60: "images/placeholder60x60.png",
    120: "images/placeholder120x120.png",
    255: "images/placeholder255x255.png",
    540: "images/placeholder540x540.png",
    1080: "images/placeholder1080x1080.png",
}

DEFAULT_PLACEHOLDER = "images/placeholder255x255.png"

SEARCH_BACKEND = "saleor.search.backends.postgresql"

AUTHENTICATION_BACKENDS = [
    "saleor.core.auth_backend.JSONWebTokenBackend",
]

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

# Change this value if your application is running behind a proxy,
# e.g. HTTP_CF_Connecting_IP for Cloudflare or X_FORWARDED_FOR
REAL_IP_ENVIRON = os.environ.get("REAL_IP_ENVIRON", "REMOTE_ADDR")

# The maximum length of a graphql query to log in tracings
OPENTRACING_MAX_QUERY_LENGTH_LOG = 2000

# Slugs for menus precreated in Django migrations
DEFAULT_MENUS = {"top_menu_name": "navbar", "bottom_menu_name": "footer"}

#  Sentry
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN, integrations=[CeleryIntegration(), DjangoIntegration()]
    )

GRAPHENE = {
    "RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST": True,
    "RELAY_CONNECTION_MAX_LIMIT": 100,
    "MIDDLEWARE": [
        "saleor.graphql.middleware.OpentracingGrapheneMiddleware",
        "saleor.graphql.middleware.JWTMiddleware",
        "saleor.graphql.middleware.app_middleware",
    ],
}

PLUGINS_MANAGER = "saleor.plugins.manager.PluginsManager"

PLUGINS = [
    "saleor.plugins.avatax.plugin.AvataxPlugin",
    "saleor.plugins.vatlayer.plugin.VatlayerPlugin",
    "saleor.plugins.webhook.plugin.WebhookPlugin",
    "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin",
    "saleor.payment.gateways.dummy_credit_card.plugin.DummyCreditCardGatewayPlugin",
    "saleor.payment.gateways.stripe.plugin.StripeGatewayPlugin",
    "saleor.payment.gateways.braintree.plugin.BraintreeGatewayPlugin",
    "saleor.payment.gateways.razorpay.plugin.RazorpayGatewayPlugin",
    "saleor.payment.gateways.adyen.plugin.AdyenGatewayPlugin",
    "saleor.plugins.invoicing.plugin.InvoicingPlugin",
]

# Plugin discovery
installed_plugins = pkg_resources.iter_entry_points("saleor.plugins")
for entry_point in installed_plugins:
    plugin_path = "{}.{}".format(entry_point.module_name, entry_point.attrs[0])
    if plugin_path not in PLUGINS:
        if entry_point.name not in INSTALLED_APPS:
            INSTALLED_APPS.append(entry_point.name)
        PLUGINS.append(plugin_path)

if (
    not DEBUG
    and ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL
    and ALLOWED_CLIENT_HOSTS == get_list(_DEFAULT_CLIENT_HOSTS)
):
    raise ImproperlyConfigured(
        "Make sure you've added storefront address to ALLOWED_CLIENT_HOSTS "
        "if ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL is enabled."
    )

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

# Default False because storefront and dashboard don't support expiration of token
JWT_EXPIRE = get_bool_from_env("JWT_EXPIRE", False)
JWT_TTL_ACCESS = timedelta(seconds=parse(os.environ.get("JWT_TTL_ACCESS", "5 minutes")))
JWT_TTL_APP_ACCESS = timedelta(
    seconds=parse(os.environ.get("JWT_TTL_APP_ACCESS", "5 minutes"))
)
JWT_TTL_REFRESH = timedelta(seconds=parse(os.environ.get("JWT_TTL_REFRESH", "30 days")))


JWT_TTL_REQUEST_EMAIL_CHANGE = timedelta(
    seconds=parse(os.environ.get("JWT_TTL_REQUEST_EMAIL_CHANGE", "1 hour")),
)
