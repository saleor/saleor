import os.path

from django.contrib.messages import constants as messages


DEBUG = True
TEMPLATE_DEBUG = DEBUG

SITE_ID = 1

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

ROOT_URLCONF = 'saleor.urls'

WSGI_APPLICATION = 'saleor.wsgi.application'

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS
INTERNAL_IPS = ['127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'dev.sqlite')
    }
}

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True
USE_TZ = True

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
SECRET_KEY = '{{ secret_key }}'

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

    # Django modules
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sitemaps',
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
    'babeldjango',
    'django_images',
    'django_prices',
    'mptt',
    'payments',
    'selectable'
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

CANONICAL_HOSTNAME = 'localhost:8000'

IMAGE_SIZES = {
    'normal': {
        'size': (750, 0)
    },
    'small': {
        'size': (280, 280),
        'crop': True
    },
    'admin': {
        'size': (50, 50),
        'crop': True
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LOGIN_URL = '/account/login'

WARN_ABOUT_INVALID_HTML5_OUTPUT = False

DEFAULT_CURRENCY = 'USD'

ACCOUNT_ACTIVATION_DAYS = 3

LOGIN_REDIRECT_URL = 'home'

FACEBOOK_APP_ID = None
FACEBOOK_SECRET = None

GOOGLE_ANALYTICS_TRACKING_ID = None
GOOGLE_CLIENT_ID = None
GOOGLE_CLIENT_SECRET = None

PAYMENT_BASE_URL = 'http://%s/' % CANONICAL_HOSTNAME

PAYMENT_MODEL = 'order.Payment'

PAYMENT_VARIANTS = {
    'default': ('payments.dummy.DummyProvider', {})
}

PAYMENT_HOST = 'localhost:8000'

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
