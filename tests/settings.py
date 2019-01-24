# pylint: disable=W0401, W0614
SECRET_KEY = 'NOTREALLY'
from saleor.settings import *  # noqa

IS_TESTING = True
import logging
from django.db import connection
connection.force_debug_cursor = True

DEFAULT_CURRENCY = 'USD'

LANGUAGE_CODE = 'en-us'

if 'sqlite' in DATABASES['default']['ENGINE']:
    DATABASES['default']['TEST'] = {  # noqa
        'SERIALIZE': False,
        'NAME': ':memory:',
        'MIRROR': None}
