from __future__ import unicode_literals

import ast
import datetime
import os.path
import raven

import dj_email_url
import django_cache_url
from django.contrib.messages import constants as messages
from dotenv import load_dotenv
load_dotenv()

DEBUG = ast.literal_eval(os.environ.get('DEBUG', 'False'))

SITE_ID = int(os.environ.get('SITE_ID', 2))

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

ROOT_URLCONF = 'saleor.urls'

WSGI_APPLICATION = 'saleor.wsgi.application'

ADMINS = (
    (
        os.environ.get('ADMIN_EMAIL_NAME', 'Your Name'),
        os.environ.get('ADMIN_EMAIL_ADDRESS', 'your_email@example.com')
    ),
)
MANAGERS = ADMINS
INTERNAL_IPS = os.environ.get('INTERNAL_IPS', '127.0.0.1').split()

redis_host = os.environ.get('REDIS_HOST', None)
redis_port = os.environ.get('REDIS_PORT', 6379)
redis_db = os.environ.get('REDIS_DB', 0)

if redis_host:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://{host}:{port}/{db}'.format(
                host=redis_host,
                port=redis_port,
                db=redis_db,
            )
        }
    }
    CONSTANCE_REDIS_CONNECTION = {
        'host': redis_host,
        'port': redis_port,
        'db': 0,
    }
else:
    CACHES = {'default': django_cache_url.config()}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'USER': os.environ.get('DB_USER'),
        'PORT': os.environ.get('DB_PORT'),
        'HOST': os.environ.get('DB_HOST'),
    }
}

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de-de'
LOCALE_PATHS = [os.path.join(PROJECT_ROOT, 'locale')]
USE_I18N = True
USE_L10N = True
USE_TZ = False

EMAIL_URL = os.environ.get('EMAIL_URL')
SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME')
SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
if not EMAIL_URL and SENDGRID_USERNAME and SENDGRID_PASSWORD:
    EMAIL_URL = 'smtp://%s:%s@smtp.sendgrid.net:587/?tls=True' % (
        SENDGRID_USERNAME, SENDGRID_PASSWORD)
email_config = dj_email_url.parse(EMAIL_URL or 'console://')

EMAIL_FILE_PATH = email_config['EMAIL_FILE_PATH']
EMAIL_HOST_USER = email_config['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = email_config['EMAIL_HOST_PASSWORD']
EMAIL_HOST = email_config['EMAIL_HOST']
EMAIL_PORT = email_config['EMAIL_PORT']
EMAIL_BACKEND = email_config['EMAIL_BACKEND']
EMAIL_USE_TLS = email_config['EMAIL_USE_TLS']
EMAIL_USE_SSL = email_config['EMAIL_USE_SSL']

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
ORDER_FROM_EMAIL = os.getenv('ORDER_FROM_EMAIL', DEFAULT_FROM_EMAIL)

MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(PROJECT_ROOT, 'media'))
MEDIA_URL = '/media/'

STATIC_ROOT = os.environ.get('STATIC_ROOT', os.path.join(PROJECT_ROOT, 'static'))
STATIC_URL = '/static/'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
]

context_processors = [
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.debug',
    'django.template.context_processors.i18n',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.template.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.template.context_processors.request',
    'saleor.core.context_processors.default_currency',
    'saleor.core.context_processors.categories',
    'saleor.core.context_processors.search_enabled',
    'saleor.site.context_processors.settings',
    'saleor.core.context_processors.webpage_schema',
    'saleor_oye.cart.context_processors.cart_counter',
]

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'OPTIONS': {
        'debug': DEBUG,
        'context_processors': context_processors,
        'string_if_invalid': '<< MISSING VARIABLE "%s" >>' if DEBUG else ''}}]

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY')

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'babeldjango.middleware.LocaleMiddleware',
    'saleor.core.middleware.CountryMiddleware',
    'saleor.core.middleware.CurrencyMiddleware',
]

INSTALLED_APPS = [
    # External apps that need to go before django's
    'storages',
    'django_nose',


    # Django modules
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.auth',
    # 'django.contrib.postgres',
    'django.contrib.admin',

    # Local apps
    'saleor.userprofile',
    'saleor.discount',
    'saleor.product',
    'saleor.cart',
    'saleor.checkout',
    'saleor.core',
    'saleor.graphql',
    # 'saleor.order',
    'saleor.dashboard',
    'saleor.shipping',
    'saleor.search',
    'saleor.site',
    'saleor.data_feeds',
    'saleor.elasticsearch',

    # External apps
    'versatileimagefield',
    # 'babeldjango',
    'django_prices',
    # 'django_prices_openexchangerates',
    'graphene_django',
    'mptt',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    # 'webpack_loader',
    'allauth',
    'allauth.account',
    'django_countries',
    'ajax_select',

    # developer stuff
    'django_extensions',

    # my proprietary oye stuff
    'saleor_oye',
    'saleor_oye.discogs',
    'saleor_oye.customers',
    'saleor_oye.payments',

    'corsheaders',
    # We authenticate via authtoken
    # 'rest_framework.authtoken',
    'constance',
    'constance.backends.database',
    'django_celery_beat',

    'robots',
    'raven.contrib.django.raven_compat',

]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'formatters': {
        'basic': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        # Make AdminEmailHandler only send error emails to admins when DEBUG is False
        # https://docs.djangoproject.com/en/1.8/topics/logging/#django.utils.log.RequireDebugFalse
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'basic',
        },
        'logstash': {
            'level': 'INFO',
            'class': 'logstash.TCPLogstashHandler',
            'host': '127.0.0.1',
            'port': 5959,  # Default value: 5959
            'version': 1,  # Version of logstash event schema. Default value: 0 (for backward compatibility of the library)
            'message_type': 'django',  # 'type' field in logstash message. Default value: 'logstash'.
            'fqdn': False,  # Fully qualified domain name. Default value: false.
            'tags': ['django.request', 'django'],  # list of tags. Default: None.
        },
    },
    # 'root': {
    #     # default logger; config for everything that propagates to the root logger
    #     'level': 'INFO',
    #     'filters': [],
    #     'handlers': ['console', 'logstash'],
    # },
    'loggers': {
        'saleor_oye': {
            'handlers': ['logstash', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['logstash', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'django.request': {
            'handlers': ['logstash'],
            'propagate': True,
        },
        'django.security': {
            'handlers': ['mail_admins'],
        },
    },
}
#
CONSTANCE_CONFIG_FIELDSETS = {
    'Public announcement': (
        'ANNOUNCEMENT_SHOW',
        'ANNOUNCEMENT_MESSAGE',
        'ANNOUNCEMENT_PRIORITY',
    ),
    'Search': (
        'SEARCH_FUZZINESS',
        'SEARCH_PREFIX_LENGTH',
        'SEARCH_PHRASE_PREFIX'
    ),
    'Payments': (
        'PAYMENTS_RECURRING_ENABLED',
        'PAYMENTS_ONECLICK_ENABLED',
        'PAYPAL_PAYMENT_ENABLED',
    ),
    'Various': (
        'MAIN_GENRE_MAP',
        'TRACK_RELEASES_UPTODATE_MINUTES',
        'DISCOGS_RELEASE_UPTODATE_HOURS',
        'VAT_RATE',
        'CHARTS_ALLOWED_ITEMS',
        'OYE_ORDERS_MAIL',
        'UNPAID_ORDER_RESERVATION_TIMEOUT_MINUTES',
        'DISCOVER_DISCOGS_RELEASES_ENABLED',
        'RESERVATION_CANCELLED_RECIPIENT',
        'SEND_RESERVATION_CANCELLED_MAIL',

    )
}
CONSTANCE_ADDITIONAL_FIELDS = {
    'priority_select': ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': (("info", "Info"), ("warning", "Warning"), ("error", "Critical"), )
    }],
}

CONSTANCE_CONFIG = {
    'MAIN_GENRE_MAP': ('', 'Holds the artificial meta genre grouping'),
    'RELEASE_INFO_UPTODATE_HOURS': (48, 'Re-evaluate tracks and discogs release after this amount of hours'),
    'TRACK_RELEASES_UPTODATE_MINUTES': (10, 'Re-evaluate tracks after this amount of hours'),
    'SEARCH_FUZZINESS': ('0', 'The maximum number of edits between input and target tokens (see https://www.elastic.co/guide/en/elasticsearch/reference/current/common-options.html#fuzziness)'),
    'SEARCH_PREFIX_LENGTH': (1, 'The minimum number of characters leading the target term'),
    'SEARCH_PHRASE_PREFIX': (True, 'Use Match Phrase Prefix instead of Match Phrase'),
    'CHARTS_ALLOWED_ITEMS': (10, 'The maximum number of allowed items in charts'),
    'VAT_RATE': (19.0, 'The current VAT tax rate'),
    'PAYMENTS_RECURRING_ENABLED': (False, 'Enable recurring payments'),
    'PAYMENTS_ONECLICK_ENABLED': (False, 'Enable oneclick payments'),
    'ANNOUNCEMENT_SHOW': (True, 'If set to True, the announcement should be shown'),
    'ANNOUNCEMENT_PRIORITY': ('info', 'Select priority', 'priority_select'),
    'ANNOUNCEMENT_MESSAGE': ('', 'Displays an announcements'),
    'OYE_ORDERS_MAIL': ('orders@oye-records.com', 'Support order mail'),
    'PAYPAL_PAYMENT_ENABLED': (False, 'If set to True Paypal payment is enabled'),
    'DISCOGS_RELEASE_UPTODATE_HOURS': (48, 'Re-evaluate discogs release after this amount of hours'),
    'UNPAID_ORDER_RESERVATION_TIMEOUT_MINUTES': (30, 'Cancel an unpaid order after this amount of minutes'),
    'DISCOVER_DISCOGS_RELEASES_ENABLED': (False, 'If set to true fetch for Discogs releases'),
    'RESERVATION_CANCELLED_RECIPIENT': ('order@oye-records.com,mail@oye-records.com', 'Comma separated list of receipients for order cancellations'),
    'SEND_RESERVATION_CANCELLED_MAIL': (False, 'If set to True a mail is send out after a reservation has been cancelled'),
    'ELASTIC_UPDATE_THRESHOLD_HOURS': (24, 'Passed hours before trying update on elastic search index item.'),
}
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

AUTH_USER_MODEL = 'saleor_oye.Kunden'

LOGIN_URL = '/account/login/'

DEFAULT_COUNTRY = 'DE'
DEFAULT_CURRENCY = 'EUR'
AVAILABLE_CURRENCIES = [DEFAULT_CURRENCY]

OPENEXCHANGERATES_API_KEY = os.environ.get('OPENEXCHANGERATES_API_KEY')

ACCOUNT_ACTIVATION_DAYS = 3

LOGIN_REDIRECT_URL = 'home'

GOOGLE_ANALYTICS_TRACKING_ID = os.environ.get('GOOGLE_ANALYTICS_TRACKING_ID')


def get_host():
    from saleor.site.utils import get_domain
    return get_domain()


PAYMENT_HOST = get_host

PAYMENT_MODEL = 'order.Payment'

PAYMENT_VARIANTS = {
    'default': ('payments.dummy.DummyProvider', {})}

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

CHECKOUT_PAYMENT_CHOICES = [
    ('default', 'Dummy provider')]

MESSAGE_TAGS = {
    messages.ERROR: 'danger'}

LOW_STOCK_THRESHOLD = 10

PAGINATE_BY = 16

BOOTSTRAP3 = {
    'set_placeholder': False,
    'set_required': False,
    'success_css_class': '',
    'form_renderers': {
        'default': 'saleor.core.utils.form_renderer.FormRenderer',
    },
}

TEST_RUNNER = 'saleor_oye.tests.legacy.ManagedModelTestRunner'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split()

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'release': [
        ('release_thumb', 'crop__100x100'),
        ('release__big', 'crop__600x600'),
        ('release__list', 'crop__380x380'),
    ],
    'artist': [
        ('artist_admin', 'crop__1200x300'),
        ('charts', 'crop__600x384'),
        ('charts_front', 'crop__410x208'),
    ],
    'charts': [
        ('charts', 'crop__600x384'),
        ('charts_front', 'crop__410x208'),
    ],
    'user': [
        ('charts', 'crop__600x384'),
        ('charts_front', 'crop__410x208'),
    ]
}

VERSATILEIMAGEFIELD_SETTINGS = {
    # Images should be pre-generated on Production environment
    'create_images_on_demand': ast.literal_eval(
        os.environ.get('CREATE_IMAGES_ON_DEMAND', 'True')),
}


ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

# We'll support couple of elasticsearch add-ons, but finally we'll use single
# variable
ES_URL = ELASTICSEARCH_URL or ''
if ES_URL:
    SEARCH_BACKENDS = {
        'default': {
            'BACKEND': 'saleor.search.backends.elasticsearch2',
            'URLS': [ES_URL],
            'INDEX': os.environ.get('ELASTICSEARCH_INDEX_NAME', 'storefront'),
            'TIMEOUT': 5,
            'AUTO_UPDATE': True},
        'dashboard': {
            'BACKEND': 'saleor.search.backends.dashboard',
            'URLS': [ES_URL],
            'INDEX': os.environ.get('ELASTICSEARCH_INDEX_NAME', 'storefront'),
            'TIMEOUT': 5,
            'AUTO_UPDATE': False}
    }
else:
    SEARCH_BACKENDS = {}

GRAPHENE = {
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware'
    ],
    'SCHEMA': 'saleor_oye.api.graphql.schema',
    'SCHEMA_OUTPUT': os.path.join(
        PROJECT_ROOT, 'saleor', 'static', 'schema.json')
}

SITE_SETTINGS_ID = 1
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 25,

}

APPEND_SLASH = True

CORS_ORIGIN_WHITELIST = [
    'google.com',
    '127.0.0.1',
    '192.168.0.3',
    '192.168.0.3:3000',
    'localhost:8000',
    'localhost:3000',
    'localhost:8080',
    '127.0.0.1:9000',
    '127.0.0.1:8000',
    '192.168.2.38:3000',
    '192.168.2.38',
    'local.oye.com:8000',
] + os.environ.get('CORS_ORIGIN_WHITELIST', '').split()

DISCOGS_CONSUMER_KEY = os.environ.get('DISCOGS_CONSUMER_KEY', None)
DISCOGS_CONSUMER_SECRET = os.environ.get('DISCOGS_CONSUMER_SECRET', None)
DISCOGS_USER_TOKEN = os.environ.get('DISCOGS_USER_TOKEN', None)

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'saleor_oye.auth.hashers.Argon2WrappedMD5PasswordHasher',
    'saleor_oye.auth.hashers.Argon2WawisysPasswordHasher'
]


AUTHENTICATION_BACKENDS = [
    'saleor_oye.auth.backends.OyePasswordAuth',
    'rest_framework.authentication.TokenAuthentication',
]

# JWT_AUTH = {
JWT_PAYLOAD_HANDLER = 'saleor_oye.auth.jwt.oye_jwt_payload_handler'
JWT_EXPIRATION_DELTA = datetime.timedelta(seconds=60 * 60)

JWT_AUTH_HEADER_PREFIX = 'JWT'
JWT_PAYLOAD_GET_USER_ID_HANDLER = 'saleor_oye.auth.jwt.jwt_get_user_id_from_payload_handler'
JWT_ALLOW_REFRESH = True

JWT_AUTH = {
    'JWT_PAYLOAD_HANDLER': 'saleor_oye.auth.jwt.oye_jwt_payload_handler',
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=60 * 60),
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    'JWT_PAYLOAD_GET_USER_ID_HANDLER': 'saleor_oye.auth.jwt.jwt_get_user_id_from_payload_handler',
    'JWT_ALLOW_REFRESH': True
}


CELERY_BROKER_URL = 'amqp://{user}:{password}@{host}:5672/{vhost}'.format(
    user=os.environ.get('RABBITMQ_USER', 'guest'),
    password=os.environ.get('RABBITMQ_PASSWORD', 'guest'),
    host=os.environ.get('RABBITMQ_HOST', 'localhost'),
    vhost=os.environ.get('RABBITMQ_VHOST', '/'),
)

CELERY_BROKER_USER = os.environ.get('RABBITMQ_USER', 'guest')
CELERY_BROKER_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', 'guest')
CELERY_BROKER_PORT = 5672
CELERY_BROKER_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
CELERY_TASK_ALWAYS_EAGER = False
# CELERY_TIMEZONE = 'Europe/Berlin'
# CELERY_TASK_ACKS_LATE = True
# CELERY_WORKER_PREFETCH_MULTIPLIER = 1
# BROKER_POOL_LIMIT


CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'cache-control',
    'x-csrftoken',
    'x-requested-with',
    'x-cart-token',
    'x-oye-token'
)


ADYEN_USER = os.environ.get('ADYEN_USER', None)
ADYEN_PASSWORD = os.environ.get('ADYEN_PASSWORD', None)
ADYEN_MERCHANT_ACCOUNT = os.environ.get('ADYEN_MERCHANT_ACCOUNT', None)
ADYEN_HMAC_SECRET = os.environ.get('ADYEN_HMAC_SECRET', None)
ADYEN_SKIN_CODE = os.environ.get('ADYEN_SKIN_CODE', None)
ADYEN_ENDPOINT_ROOT= os.environ.get('ADYEN_ENDPOINT_ROOT', None)
ADYEN_PAYMENT_OPTIONS_HPP = os.environ.get('ADYEN_PAYMENT_OPTIONS_HPP', None)

PASSWORD_CONFIRMATION_TIMEOUT_DAYS = 1

#
PAYPAL_LOG_URL = os.environ.get('PAYPAL_LOG_URL', None)
PAYPAL_API_URL = os.environ.get('PAYPAL_API_URL', None)
PAYPAL_API_USER = os.environ.get('PAYPAL_API_USER', None)
PAYPAL_API_PWD = os.environ.get('PAYPAL_API_PWD', None)
PAYPAL_API_SIG = os.environ.get('PAYPAL_API_SIG', None)
PAYPAL_API_VERSION = os.environ.get('PAYPAL_API_VERSION', None)


PDF_STORAGE_ROOT = os.environ.get('PDF_STORAGE_ROOT', '/tmp/')
ORIGINAL_IMAGES_ROOT = os.environ.get('ORIGINAL_IMAGES_ROOT', '/var/www/images/')

ENVIRONMENT = os.environ.get('ENVIRONMENT', None)

REMOTE = ast.literal_eval(os.environ.get('REMOTE', 'False'))

RAVEN_CONFIG = {
    'dsn': 'https://{public_key}:{secret}@{host}/{project_id}'.format(
        public_key=os.environ.get('SENTRY_PUBLIC_KEY'),
        secret=os.environ.get('SENTRY_SECRET_KEY'),
        host=os.environ.get('SENTRY_HOST'),
        project_id=os.environ.get('SENTRY_PROJECT_ID'),
    ),
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    # 'release': raven.fetch_git_sha(os.path.abspath(os.pardir)),
}


MAILCHIMP_API_KEY = os.environ.get('MAILCHIMP_API_KEY')
MAILCHIMP_USER = os.environ.get('MAILCHIMP_USER')
MAILCHIMP_DEFAULT_LIST_ID = os.environ.get('MAILCHIMP_DEFAULT_LIST_ID')
