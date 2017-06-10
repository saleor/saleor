from __future__ import unicode_literals

import ast
import datetime
import os.path

import dj_email_url
import django_cache_url
from django.contrib.messages import constants as messages

DEBUG = ast.literal_eval(os.environ.get('DEBUG', 'False'))

SITE_ID = 1

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

if os.environ.get('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL')
        }
    }
else:
    CACHES = {'default': django_cache_url.config()}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('RECORDSHOP_LEGACY_DB_NAME'),
        'PASSWORD': os.environ.get('RECORDSHOP_LEGACY_DB_PASSWORD'),
        'USER': os.environ.get('RECORDSHOP_LEGACY_DB_USER'),
        'PORT': os.environ.get('RECORDSHOP_LEGACY_DB_PORT'),
        'HOST': os.environ.get('RECORDSHOP_LEGACY_DB_HOST'),
    }
}

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de-de'
LOCALE_PATHS = [os.path.join(PROJECT_ROOT, 'locale')]
USE_I18N = True
USE_L10N = True
USE_TZ = True

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
# STATICFILES_DIRS = [
#     ('images', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'images'))
# ]
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

loaders = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # TODO: this one is slow, but for now need for mptt?
    'django.template.loaders.eggs.Loader']

if not DEBUG:
    loaders = [('django.template.loaders.cached.Loader', loaders)]

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(PROJECT_ROOT, 'templates')],
    'OPTIONS': {
        'debug': DEBUG,
        'context_processors': context_processors,
        'loaders': loaders,
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
    'saleor.core.middleware.DiscountMiddleware',
    'saleor.core.middleware.GoogleAnalytics',
    'saleor.core.middleware.CountryMiddleware',
    'saleor.core.middleware.CurrencyMiddleware',
]

INSTALLED_APPS = [
    # External apps that need to go before django's
    'storages',

    # Django modules
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'django.contrib.postgres',
    'django.contrib.admin',

    # Local apps
    'saleor.userprofile',
    'saleor.discount',
    'saleor.product',
    'saleor.cart',
    'saleor.checkout',
    'saleor.core',
    'saleor.graphql',
    'saleor.order',
    'saleor.dashboard',
    'saleor.shipping',
    'saleor.search',
    'saleor.site',
    'saleor.data_feeds',
    'saleor.elasticsearch',

    # External apps
    'versatileimagefield',
    'babeldjango',
    'bootstrap3',
    'django_prices',
    'django_prices_openexchangerates',
    'emailit',
    'graphene_django',
    'mptt',
    'payments',
    'materializecssform',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    'webpack_loader',
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
    # 'saleor_oye.payments',

    'corsheaders',
    # We authenticate via authtoken
    # 'rest_framework.authtoken',
    'constance',
    'django_celery_beat',
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
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'basic',
        },
    },
    'root': {
        # default logger; config for everything that propagates to the root logger
        'level': 'INFO',
        'filters': [],
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django.request': {
            'handlers': ['mail_admins'],
        },
        'django.security': {
            'handlers': ['mail_admins'],
        },

    },
}

CONSTANCE_CONFIG = {
    'MAIN_GENRE_MAP': ('', 'Holds the artificial meta genre grouping'),
    'RELEASE_INFO_UPTODATE_HOURS': (48, 'Re-evaluate tracks and discogs release after this amount of hours'),
    'SEARCH_FUZZINESS': ('0', 'The maximum number of edits between input and target tokens (see https://www.elastic.co/guide/en/elasticsearch/reference/current/common-options.html#fuzziness)'),
    'SEARCH_PREFIX_LENGTH': (1, 'The minimum number of characters leading the target term'),
    'CHARTS_ALLOWED_ITEMS': (10, 'The maximum number of allowed items in charts')
}

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
MAX_CART_LINE_QUANTITY = os.environ.get('MAX_CART_LINE_QUANTITY', 50)

PAGINATE_BY = 16

BOOTSTRAP3 = {
    'set_placeholder': False,
    'set_required': False,
    'success_css_class': '',
    'form_renderers': {
        'default': 'saleor.core.utils.form_renderer.FormRenderer',
    },
}

TEST_RUNNER = ''

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split()

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# disable to avoid costs during development
USE_AWS = os.environ.get('USE_AWS', False)

# Amazon S3 configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_MEDIA_BUCKET_NAME = os.environ.get('AWS_MEDIA_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')
AWS_QUERYSTRING_AUTH = ast.literal_eval(
    os.environ.get('AWS_QUERYSTRING_AUTH', 'False'))

if USE_AWS and AWS_STORAGE_BUCKET_NAME:
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

if USE_AWS and AWS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'saleor.core.storages.S3MediaStorage'
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'defaults': [
        ('list_view', 'crop__100x100'),
        ('dashboard', 'crop__400x400'),
        ('product_page_mobile', 'crop__680x680'),
        ('product_page_big', 'crop__750x750'),
        ('product_page_thumb', 'crop__280x280')]}

VERSATILEIMAGEFIELD_SETTINGS = {
    # Images should be pre-generated on Production environment
    'create_images_on_demand': ast.literal_eval(
        os.environ.get('CREATE_IMAGES_ON_DEMAND', 'True')),
}

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'assets/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'webpack-bundle.json'),
        'POLL_INTERVAL': 0.1,
        'IGNORE': [
            r'.+\.hot-update\.js',
            r'.+\.map']}}

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_SESSION_REMEMBER = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_FORMS = {
    'reset_password_from_key': 'saleor.userprofile.forms.SetPasswordForm'
}

ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
SEARCHBOX_URL = os.environ.get('SEARCHBOX_URL')
BONSAI_URL = os.environ.get('BONSAI_URL')
# We'll support couple of elasticsearch add-ons, but finally we'll use single
# variable
ES_URL = ELASTICSEARCH_URL or SEARCHBOX_URL or BONSAI_URL or ''
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
        # 'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 25,

}

APPEND_SLASH = True

CORS_ORIGIN_WHITELIST = [
    'google.com',
    'localhost:8000',
    'localhost:3000',
    'localhost:8080',
    '127.0.0.1:9000',
    'local.oye.com:8000',
] + os.environ.get('CORS_ORIGIN_WHITELIST', '').split()

DISCOGS_CONSUMER_KEY = os.environ.get('DISCOGS_CONSUMER_KEY', None)
DISCOGS_CONSUMER_SECRET = os.environ.get('DISCOGS_CONSUMER_SECRET', None)
DISCOGS_USER_TOKEN = os.environ.get('DISCOGS_USER_TOKEN', None)

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'saleor_oye.auth.hashers.Argon2WrappedMD5PasswordHasher'
]



AUTHENTICATION_BACKENDS = [
#    'saleor_oye.auth.backends.OyeTokenAuth',
    'saleor_oye.auth.backends.OyePasswordAuth',
    'rest_framework.authentication.TokenAuthentication',
]

# JWT_AUTH = {
JWT_PAYLOAD_HANDLER = 'saleor_oye.auth.jwt.oye_jwt_payload_handler'
JWT_EXPIRATION_DELTA = datetime.timedelta(seconds=60 * 60)
# JWT_AUTH_COOKIE = 'jwt'
JWT_AUTH_HEADER_PREFIX = 'JWT'
JWT_PAYLOAD_GET_USER_ID_HANDLER = 'saleor_oye.auth.jwt.jwt_get_user_id_from_payload_handler'
JWT_ALLOW_REFRESH = True

JWT_AUTH = {
    'JWT_PAYLOAD_HANDLER': 'saleor_oye.auth.jwt.oye_jwt_payload_handler',
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=60 * 60),
    # 'JWT_AUTH_COOKIE': 'jwt',
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    'JWT_PAYLOAD_GET_USER_ID_HANDLER': 'saleor_oye.auth.jwt.jwt_get_user_id_from_payload_handler',
    'JWT_ALLOW_REFRESH': True
}


CELERY_BROKER_URL = 'amqp://{user}:{password}@localhost:5672//'.format(
    user=os.environ.get('RABBITMQ_USER', 'guest'),
    password=os.environ.get('RABBITMQ_PASSWORD', 'guest'),
    # vhost=os.environ.get('RABBITMQ_VHOST', '/'),
)

CELERY_BROKER_USER = os.environ.get('RABBITMQ_USER', 'guest')
CELERY_BROKER_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', 'guest')
CELERY_BROKER_PORT = 5672
CELERY_BROKER_HOST = 'localhost'
# CELERY_ALWAYS_EAGER = False


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
