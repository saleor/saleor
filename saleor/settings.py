import ast
import os.path

import dj_database_url
import dj_email_url
import django_cache_url
from django.contrib.messages import constants as messages
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_prices.templatetags.prices_i18n import get_currency_fraction
import environ
from email.utils import getaddresses

from . import __version__

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, True),
    INTERNAL_IPS=(list, []),
    SALEOR_LANGUAGES=(list, []),
    ENABLE_SSL=(bool, False),
    ENABLE_SILK=(bool, False),
    VATLAYER_USE_HTTPS=(bool, False),
    ALLOWED_HOSTS=(list, []),
    AWS_QUERYSTRING_AUTH=(bool, False),
    CREATE_IMAGES_ON_DEMAND=(bool, True),
    MAX_CART_LINE_QUANTITY=(int, 50)
)

env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))  # noqa
environ.Env.read_env(env_file=env_file)


# def get_list(text):
#     return [item.strip() for item in text.split(',')]
#
#
# def get_bool_from_env(name, default_value):
#     if name in os.environ:
#         value = os.environ[name]
#         try:
#             return ast.literal_eval(value)
#         except ValueError as e:
#             raise ValueError(
#                 '{} is an invalid value for {}'.format(value, name)) from e
#     return default_value


DEBUG = env('DEBUG', default=True)

SITE_ID = 1

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

ROOT_URLCONF = 'saleor.urls'

WSGI_APPLICATION = 'saleor.wsgi.application'

ADMINS = getaddresses([env('DJANGO_ADMINS')])
MANAGERS = ADMINS

# INTERNAL_IPS = get_list(env('INTERNAL_IPS', '127.0.0.1'))
INTERNAL_IPS = env('INTERNAL_IPS', default='127.0.0.1')

# Some cloud providers like Heroku export REDIS_URL variable instead of CACHE_URL
REDIS_URL = env.cache('REDIS_URL')
# if REDIS_URL:
#     CACHE_URL = env.cache('CACHE_URL', REDIS_URL)
# CACHES = {'default': django_cache_url.config()}
CACHES = {'default': REDIS_URL}


DATABASES = {
    'default': dj_database_url.config(
        default=env.db(),
        conn_max_age=600)}


TIME_ZONE = env('TIME_ZONE', default='America/Chicago')
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('bg', _('Bulgarian')),
    ('cs', _('Czech')),
    ('de', _('German')),
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fa-ir', _('Persian (Iran)')),
    ('fr', _('French')),
    ('hu', _('Hungarian')),
    ('it', _('Italian')),
    ('ja', _('Japanese')),
    ('ko', _('Korean')),
    ('nb', _('Norwegian')),
    ('nl', _('Dutch')),
    ('pl', _('Polish')),
    ('pt-br', _('Portuguese (Brazil)')),
    ('ro', _('Romanian')),
    ('ru', _('Russian')),
    ('sk', _('Slovak')),
    ('tr', _('Turkish')),
    ('uk', _('Ukrainian')),
    ('vi', _('Vietnamese')),
    ('zh-hans', _('Chinese')),
    ('zh-tw', _('Chinese (Taiwan)'))]

_tmp = env('SALEOR_LANGUAGES')
if _tmp:
    LANGUAGES = [i for i in LANGUAGES if i[0] in _tmp]


LOCALE_PATHS = [os.path.join(PROJECT_ROOT, 'locale')]
USE_I18N = True
USE_L10N = True
USE_TZ = True

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

EMAIL_URL = env.email_url('EMAIL_URL')
EMAIL_URL = env('EMAIL_URL')
SENDGRID_USERNAME = env('SENDGRID_USERNAME', default='')
SENDGRID_PASSWORD = env('SENDGRID_PASSWORD', default='')
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

ENABLE_SSL = env('ENABLE_SSL', default=False)

if ENABLE_SSL:
    SECURE_SSL_REDIRECT = not DEBUG

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
ORDER_FROM_EMAIL = env('ORDER_FROM_EMAIL', default=DEFAULT_FROM_EMAIL)

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
MEDIA_URL = env('MEDIA_URL', default='/media/')

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
STATIC_URL = env('STATIC_URL', default='/static/')
STATICFILES_DIRS = [
    ('assets', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'assets')),
    ('favicons', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'favicons')),
    ('images', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'images')),
    ('dashboard', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'dashboard'))]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder']

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
    'saleor.checkout.context_processors.cart_counter',
    'saleor.core.context_processors.search_enabled',
    'saleor.site.context_processors.site',
    'social_django.context_processors.backends',
    'social_django.context_processors.login_redirect']

loaders = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader']

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
SECRET_KEY = env('SECRET_KEY')

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django_babel.middleware.LocaleMiddleware',
    'saleor.core.middleware.discounts',
    'saleor.core.middleware.google_analytics',
    'saleor.core.middleware.country',
    'saleor.core.middleware.currency',
    'saleor.core.middleware.site',
    'saleor.core.middleware.taxes',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'impersonate.middleware.ImpersonateMiddleware',
    'saleor.graphql.middleware.jwt_middleware'
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
    'django.forms',

    # Local apps
    'saleor.account',
    'saleor.discount',
    'saleor.product',
    'saleor.checkout',
    'saleor.core',
    'saleor.graphql',
    'saleor.menu',
    'saleor.order.OrderAppConfig',
    'saleor.dashboard',
    'saleor.seo',
    'saleor.shipping',
    'saleor.search',
    'saleor.site',
    'saleor.data_feeds',
    'saleor.page',

    # External apps
    'versatileimagefield',
    'django_babel',
    'bootstrap4',
    'django_measurement',
    'django_prices',
    'django_prices_openexchangerates',
    'django_prices_vatlayer',
    'graphene_django',
    'mptt',
    'payments',
    'webpack_loader',
    'social_django',
    'django_countries',
    'django_filters',
    'django_celery_results',
    'impersonate',
    'phonenumber_field',
    'captcha']

if DEBUG:
    MIDDLEWARE.append(
        'debug_toolbar.middleware.DebugToolbarMiddleware')
    INSTALLED_APPS.append('debug_toolbar')
    DEBUG_TOOLBAR_PANELS = [
        # adds a request history to the debug toolbar
        'ddt_request_history.panels.request_history.RequestHistoryPanel',

        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ]
    DEBUG_TOOLBAR_CONFIG = {
        'RESULTS_STORE_SIZE': 100}

ENABLE_SILK = env('ENABLE_SILK', False)
if ENABLE_SILK:
    MIDDLEWARE.insert(0, 'silk.middleware.SilkyMiddleware')
    INSTALLED_APPS.append('silk')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'INFO',
        'handlers': ['console']},
    'formatters': {
        'verbose': {
            'format': (
                '%(levelname)s %(name)s %(message)s'
                ' [PID:%(process)d:%(threadName)s]')},
        'simple': {
            'format': '%(levelname)s %(message)s'}},
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'}},
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'},
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'}},
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            'propagate': True},
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True},
        'saleor': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True}}}

AUTH_USER_MODEL = 'account.User'

LOGIN_URL = '/account/login/'

DEFAULT_COUNTRY = env('DEFAULT_COUNTRY', default='US')
DEFAULT_CURRENCY = env('DEFAULT_CURRENCY', default='USD')
DEFAULT_DECIMAL_PLACES = get_currency_fraction(DEFAULT_CURRENCY)
AVAILABLE_CURRENCIES = [DEFAULT_CURRENCY]
COUNTRIES_OVERRIDE = {
    'EU': pgettext_lazy(
        'Name of political and economical union of european countries',
        'European Union')}

OPENEXCHANGERATES_API_KEY = env('OPENEXCHANGERATES_API_KEY', default='')

# VAT configuration
# Enabling vat requires valid vatlayer access key.
# If you are subscribed to a paid vatlayer plan, you can enable HTTPS.
VATLAYER_ACCESS_KEY = env('VATLAYER_ACCESS_KEY', default='')
VATLAYER_USE_HTTPS = env('VATLAYER_USE_HTTPS', default=False)

ACCOUNT_ACTIVATION_DAYS = 3

LOGIN_REDIRECT_URL = 'home'

GOOGLE_ANALYTICS_TRACKING_ID = env('GOOGLE_ANALYTICS_TRACKING_ID',default='')


def get_host():
    from django.contrib.sites.models import Site
    return Site.objects.get_current().domain


PAYMENT_HOST = get_host

PAYMENT_MODEL = 'order.Payment'

PAYMENT_VARIANTS = {
    'default': ('payments.dummy.DummyProvider', {})}

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# Do not use cached session if locmem cache backend is used but fallback to use
# default django.contrib.sessions.backends.db instead
if not CACHES['default']['BACKEND'].endswith('LocMemCache'):
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

CHECKOUT_PAYMENT_CHOICES = [
    ('default', 'Dummy provider')]

MESSAGE_TAGS = {
    messages.ERROR: 'danger'}

LOW_STOCK_THRESHOLD = 10
MAX_CART_LINE_QUANTITY = env('MAX_CART_LINE_QUANTITY', default=50)

PAGINATE_BY = 16
DASHBOARD_PAGINATE_BY = 30
DASHBOARD_SEARCH_LIMIT = 5

bootstrap4 = {
    'set_placeholder': False,
    'set_required': False,
    'success_css_class': '',
    'form_renderers': {
        'default': 'saleor.core.utils.form_renderer.FormRenderer'}}

TEST_RUNNER = ''

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='localhost,127.0.0.1')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Amazon S3 configuration
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_LOCATION = env('AWS_LOCATION', default='')
AWS_MEDIA_BUCKET_NAME = env('AWS_MEDIA_BUCKET_NAME', default='')
AWS_MEDIA_CUSTOM_DOMAIN = env('AWS_MEDIA_CUSTOM_DOMAIN', default='')
AWS_QUERYSTRING_AUTH = env('AWS_QUERYSTRING_AUTH', default=False)
AWS_S3_CUSTOM_DOMAIN = env('AWS_STATIC_CUSTOM_DOMAIN', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='')

if AWS_STORAGE_BUCKET_NAME:
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

if AWS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'saleor.core.storages.S3MediaStorage'
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'products': [
        ('product_gallery', 'thumbnail__540x540'),
        ('product_gallery_2x', 'thumbnail__1080x1080'),
        ('product_small', 'thumbnail__60x60'),
        ('product_small_2x', 'thumbnail__120x120'),
        ('product_list', 'thumbnail__255x255'),
        ('product_list_2x', 'thumbnail__510x510')]}

VERSATILEIMAGEFIELD_SETTINGS = {
    # Images should be pre-generated on Production environment
    'create_images_on_demand': env(
        'CREATE_IMAGES_ON_DEMAND', default=DEBUG),
}

PLACEHOLDER_IMAGES = {
    60: 'images/placeholder60x60.png',
    120: 'images/placeholder120x120.png',
    255: 'images/placeholder255x255.png',
    540: 'images/placeholder540x540.png',
    1080: 'images/placeholder1080x1080.png'}

DEFAULT_PLACEHOLDER = 'images/placeholder255x255.png'

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'assets/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'webpack-bundle.json'),
        'POLL_INTERVAL': 0.1,
        'IGNORE': [
            r'.+\.hot-update\.js',
            r'.+\.map']}}


LOGOUT_ON_PASSWORD_CHANGE = False

# SEARCH CONFIGURATION
DB_SEARCH_ENABLED = True

# support deployment-dependant elastic enviroment variable
ES_URL = (env('ELASTICSEARCH_URL', default='') or
          env('SEARCHBOX_URL', default='') or env('BONSAI_URL', default=''))

ENABLE_SEARCH = bool(ES_URL) or DB_SEARCH_ENABLED  # global search disabling

SEARCH_BACKEND = 'saleor.search.backends.postgresql'

if ES_URL:
    SEARCH_BACKEND = 'saleor.search.backends.elasticsearch'
    INSTALLED_APPS.append('django_elasticsearch_dsl')
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': ES_URL}}

AUTHENTICATION_BACKENDS = [
    'saleor.account.backends.facebook.CustomFacebookOAuth2',
    'saleor.account.backends.google.CustomGoogleOAuth2',
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend']

SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details']

SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, email'}
# As per March 2018, Facebook requires all traffic to go through HTTPS only
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

# CELERY SETTINGS
CELERY_BROKER_URL = env(
    'CELERY_BROKER_URL', default=env('CLOUDAMQP_URL', default='')) or ''
CELERY_TASK_ALWAYS_EAGER = False if CELERY_BROKER_URL else True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'

# Impersonate module settings
IMPERSONATE = {
    'URI_EXCLUSIONS': [r'^dashboard/'],
    'CUSTOM_USER_QUERYSET': 'saleor.account.impersonate.get_impersonatable_users',  # noqa
    'USE_HTTP_REFERER': True,
    'CUSTOM_ALLOW': 'saleor.account.impersonate.can_impersonate'}


# Rich-text editor
ALLOWED_TAGS = [
    'a',
    'b',
    'blockquote',
    'br',
    'em',
    'h2',
    'h3',
    'i',
    'img',
    'li',
    'ol',
    'p',
    'strong',
    'ul']
ALLOWED_ATTRIBUTES = {
    '*': ['align', 'style'],
    'a': ['href', 'title'],
    'img': ['src']}
ALLOWED_STYLES = ['text-align']


# Slugs for menus precreated in Django migrations
DEFAULT_MENUS = {
    'top_menu_name': 'navbar',
    'bottom_menu_name': 'footer'}

# This enable the new 'No Captcha reCaptcha' version (the simple checkbox)
# instead of the old (deprecated) one. For more information see:
#   https://github.com/praekelt/django-recaptcha/blob/34af16ba1e/README.rst
NOCAPTCHA = True

# Set Google's reCaptcha keys
RECAPTCHA_PUBLIC_KEY = env('RECAPTCHA_PUBLIC_KEY', default='')
RECAPTCHA_PRIVATE_KEY = env('RECAPTCHA_PRIVATE_KEY', default='')


#  Sentry
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')
    RAVEN_CONFIG = {
        'dsn': SENTRY_DSN,
        'release': __version__}


SERIALIZATION_MODULES = {
    'json': 'saleor.core.utils.json_serializer'}
