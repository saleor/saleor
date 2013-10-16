import os.path

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
        'NAME': 'dev.sqlite',
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
    os.path.join(PROJECT_ROOT, 'saleor', 'static'),
]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
]

TEMPLATE_DIRS = [
    os.path.join(PROJECT_ROOT, 'saleor', 'templates'),
]
TEMPLATE_LOADERS = [
    'django.template.loaders.app_directories.Loader',
    # TODO: this one is slow, but for now need for mptt?
    'django.template.loaders.eggs.Loader',
]

# Make this unique, and don't share it with anybody.
SECRET_KEY = '{{ secret_key }}'

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'cart.middleware.CartMiddleware',
    'saleor.middleware.CheckHTML',
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
    'saleor.context_processors.googe_analytics',
    'saleor.context_processors.canonical_hostname',
    'saleor.context_processors.default_currency',
]

INSTALLED_APPS = [
    # External apps that need to go before django's

    # Django modules
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.webdesign',

    # External apps
    'south',
    'django_prices',
    'mptt',
    'payments',

    # Local apps
    'saleor',
    'product',
    'cart',
    'checkout',
    'order',
    'userprofile',
    'registration',
    'payment',
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
            'propagate': True,
        },
        'saleor': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

AUTHENTICATION_BACKENDS = (
    'registration.backends.EmailPasswordBackend',
    'registration.backends.ExternalLoginBackend',
    'registration.backends.TrivialBackend',
)

AUTH_USER_MODEL = 'userprofile.User'

CANONICAL_HOSTNAME = 'localhost:8000'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LOGIN_URL = '/account/login'

WARN_ABOUT_INVALID_HTML5_OUTPUT = False

SATCHLESS_DEFAULT_CURRENCY = 'USD'

ACCOUNT_ACTIVATION_DAYS = 3

LOGIN_REDIRECT_URL = "home"

FACEBOOK_APP_ID = "YOUR_FACEBOOK_APP_ID"

FACEBOOK_SECRET = "YOUR_FACEBOOK_APP_SECRET"

GOOGLE_CLIENT_ID = "YOUR_GOOGLE_APP_ID"

GOOGLE_SECRET = "YOUR_GOOGLE_APP_SECRET"

PAYMENT_BASE_URL = 'http://%s/' % CANONICAL_HOSTNAME

PAYMENT_MODEL = "payment.Payment"

PAYMENT_VARIANTS = {
    'default': ('payments.dummy.DummyProvider', {'url': 'http://google.pl/'}),
}

CHECKOUT_PAYMENT_CHOICES = [
    ('default', 'Dummy provider')
]
