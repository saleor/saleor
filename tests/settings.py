# pylint: disable=W0401, W0614
from saleor.settings import *  # noqa

CELERY_TASK_ALWAYS_EAGER = True

SECRET_KEY = 'NOTREALLY'

DEFAULT_CURRENCY = 'USD'

LANGUAGE_CODE = 'en'

ES_URL = None
SEARCH_BACKEND = 'saleor.search.backends.postgresql'
INSTALLED_APPS = [a for a in INSTALLED_APPS if a != 'django_elasticsearch_dsl']

RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''

VATLAYER_ACCESS_KEY = ''

if 'sqlite' in DATABASES['default']['ENGINE']:  # noqa
    DATABASES['default']['TEST'] = {  # noqa
        'SERIALIZE': False,
        'NAME': ':memory:',
        'MIRROR': None}

CHECKOUT_PAYMENT_GATEWAYS = {
    DUMMY: 'Dummy gateway',
    BRAINTREE: 'Braintree',
    RAZORPAY: 'Razorpay',
    STRIPE: 'Stripe'
}

COUNTRIES_ONLY = None

MEDIA_ROOT = None
MAX_CHECKOUT_LINE_QUANTITY = 50
