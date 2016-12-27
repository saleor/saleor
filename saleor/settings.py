from __future__ import unicode_literals

import ast
import os.path

import dj_database_url
import dj_email_url
from django.contrib.messages import constants as messages
import django_cache_url


DEBUG = ast.literal_eval(os.environ.get('DEBUG', 'True'))

SITE_ID = 1

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

ROOT_URLCONF = 'saleor.urls'

WSGI_APPLICATION = 'saleor.wsgi.application'

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS
INTERNAL_IPS = os.environ.get('INTERNAL_IPS', '127.0.0.1').split()

CACHES = {'default': django_cache_url.config()}

if os.environ.get('REDIS_URL'):
    CACHES['default'] = {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL')}

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://saleor:saleor@localhost:5432/saleor',
        conn_max_age=600)}


TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
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


MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, 'saleor', 'static')
]
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
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'babeldjango.middleware.LocaleMiddleware',
    'saleor.core.middleware.DiscountMiddleware',
    'saleor.core.middleware.GoogleAnalytics',
    'saleor.core.middleware.CountryMiddleware',
    'saleor.core.middleware.CurrencyMiddleware'
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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.postgres',

    # Local apps
    'saleor.userprofile',
    'saleor.discount',
    'saleor.product',
    'saleor.cart',
    'saleor.checkout',
    'saleor.core',
    'saleor.order',
    'saleor.dashboard',
    'saleor.shipping',
    'saleor.search',
    'saleor.data_feeds',

    # External apps
    'versatileimagefield',
    'babeldjango',
    'bootstrap3',
    'django_prices',
    'django_prices_openexchangerates',
    'emailit',
    'mptt',
    'payments',
    'selectable',
    'materializecssform',
    'rest_framework',
    'webpack_loader',
    'allauth',
    'allauth.account',
    'allauth.socialaccount'
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True
        },
        'saleor': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

AUTH_USER_MODEL = 'userprofile.User'

LOGIN_URL = '/account/login'

DEFAULT_COUNTRY = 'US'
DEFAULT_CURRENCY = 'USD'
AVAILABLE_CURRENCIES = [DEFAULT_CURRENCY]
DEFAULT_WEIGHT = 'lb'

OPENEXCHANGERATES_API_KEY = os.environ.get('OPENEXCHANGERATES_API_KEY')

ACCOUNT_ACTIVATION_DAYS = 3

LOGIN_REDIRECT_URL = 'home'

FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
FACEBOOK_SECRET = os.environ.get('FACEBOOK_SECRET')

GOOGLE_ANALYTICS_TRACKING_ID = os.environ.get('GOOGLE_ANALYTICS_TRACKING_ID')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

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
    'success_css_class': ''}

TEST_RUNNER = ''

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split()

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Amazon S3 configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_MEDIA_BUCKET_NAME = os.environ.get('AWS_MEDIA_BUCKET_NAME')
AWS_QUERYSTRING_AUTH = ast.literal_eval(
    os.environ.get('AWS_QUERYSTRING_AUTH', 'False'))

if AWS_STORAGE_BUCKET_NAME:
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

if AWS_MEDIA_BUCKET_NAME:
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
SOCIALACCOUNT_EMAIL_VERIFICATION = False
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_ADAPTER = 'saleor.userprofile.adapters.AccountAdapter'


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
