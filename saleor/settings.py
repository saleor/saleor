import os.path

import dj_database_url
from django.contrib.messages import constants as messages


DEBUG = bool(os.environ.get('DEBUG', False))
TEMPLATE_DEBUG = DEBUG

SITE_ID = 1

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

ROOT_URLCONF = 'saleor.urls'

WSGI_APPLICATION = 'saleor.wsgi.application'

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS
INTERNAL_IPS = os.environ.get('INTERNAL_IPS', '127.0.0.1').split()

SQLITE_DB_URL = 'sqlite:///' + os.path.join(PROJECT_ROOT, 'dev.sqlite')

DATABASES = {'default': dj_database_url.config(default=SQLITE_DB_URL)}


TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True
USE_TZ = True

EMAIL_BACKEND = ('django.core.mail.backends.%s.EmailBackend' %
                 os.environ.get('EMAIL_BACKEND_MODULE', 'console'))
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_USE_TLS = bool(os.environ.get('EMAIL_USE_TLS', False))
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')


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

TEMPLATE_DIRS = [
    os.path.join(PROJECT_ROOT, 'templates')
]
TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # TODO: this one is slow, but for now need for mptt?
    'django.template.loaders.eggs.Loader'
]

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY', '{{ secret_key }}')

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'babeldjango.middleware.LocaleMiddleware',
    'saleor.cart.middleware.CartMiddleware',
    'saleor.core.middleware.DiscountMiddleware',
    'saleor.core.middleware.GoogleAnalytics',
    'saleor.core.middleware.CheckHTML'
]

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'saleor.core.context_processors.canonical_hostname',
    'saleor.core.context_processors.default_currency'
]

INSTALLED_APPS = [
    # External apps that need to go before django's
    'offsite_storage',

    # Django modules
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.webdesign',

    # Local apps
    'saleor.cart',
    'saleor.checkout',
    'saleor.core',
    'saleor.product',
    'saleor.order',
    'saleor.registration',
    'saleor.userprofile',
    'saleor.dashboard',

    # External apps
    'versatileimagefield',
    'babeldjango',
    'django_prices',
    'emailit',
    'mptt',
    'payments',
    'selectable',
    'materializecssform',
    'rest_framework',
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

AUTHENTICATION_BACKENDS = (
    'saleor.registration.backends.EmailPasswordBackend',
    'saleor.registration.backends.ExternalLoginBackend',
    'saleor.registration.backends.TrivialBackend'
)

AUTH_USER_MODEL = 'userprofile.User'

CANONICAL_HOSTNAME = os.environ.get('CANONICAL_HOSTNAME', 'localhost:8000')

LOGIN_URL = '/account/login'

WARN_ABOUT_INVALID_HTML5_OUTPUT = False

DEFAULT_CURRENCY = 'USD'
DEFAULT_WEIGHT = 'lb'

ACCOUNT_ACTIVATION_DAYS = 3

LOGIN_REDIRECT_URL = 'home'

FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
FACEBOOK_SECRET = os.environ.get('FACEBOOK_SECRET')

GOOGLE_ANALYTICS_TRACKING_ID = os.environ.get('GOOGLE_ANALYTICS_TRACKING_ID')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

PAYMENT_BASE_URL = 'http://%s/' % CANONICAL_HOSTNAME

PAYMENT_MODEL = 'order.Payment'

PAYMENT_VARIANTS = {
    'default': ('payments.dummy.DummyProvider', {})
}

PAYMENT_HOST = os.environ.get('PAYMENT_HOST', 'localhost:8000')

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

CHECKOUT_PAYMENT_CHOICES = [
    ('default', 'Dummy provider')
]

TEMPLATE_STRING_IF_INVALID = '<< MISSING VARIABLE >>'

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

LOW_STOCK_THRESHOLD = 10

TEST_RUNNER = ''

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split()

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Amazon S3 configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STATIC_BUCKET_NAME = os.environ.get('AWS_STATIC_BUCKET_NAME')

AWS_MEDIA_ACCESS_KEY_ID = os.environ.get('AWS_MEDIA_ACCESS_KEY_ID')
AWS_MEDIA_SECRET_ACCESS_KEY = os.environ.get('AWS_MEDIA_SECRET_ACCESS_KEY')
AWS_MEDIA_BUCKET_NAME = os.environ.get('AWS_MEDIA_BUCKET_NAME')

if AWS_STATIC_BUCKET_NAME:
    STATICFILES_STORAGE = 'offsite_storage.storages.CachedS3FilesStorage'

if AWS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'offsite_storage.storages.S3MediaStorage'
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
