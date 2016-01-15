from .settings import *

SECRET_KEY = 'NOTREALLY'

DEFAULT_CURRENCY = 'USD'

DATABASES['default']['TEST'] = {
    'SERIALIZE': False,
    'NAME': ':memory:',
    'MIRROR': None}
