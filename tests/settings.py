# pylint: disable=I0011, W0401, W0614
from saleor.settings import *  # noqa

SECRET_KEY = 'NOTREALLY'

DEFAULT_CURRENCY = 'USD'

DATABASES['default']['TEST'] = {  # noqa
    'SERIALIZE': False,
    'NAME': ':memory:',
    'MIRROR': None}
