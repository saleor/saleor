from __future__ import absolute_import

VERSION = (6, 3, 1)
__version__ = VERSION
__versionstr__ = '.'.join(map(str, VERSION))

import sys

if (2, 7) <= sys.version_info < (3, 2):
    # On Python 2.7 and Python3 < 3.2, install no-op handler to silence
    # `No handlers could be found for logger "elasticsearch"` message per
    # <https://docs.python.org/2/howto/logging.html#configuring-logging-for-a-library>
    import logging
    logger = logging.getLogger('elasticsearch')
    logger.addHandler(logging.NullHandler())

from .client import Elasticsearch
from .transport import Transport
from .connection_pool import ConnectionPool, ConnectionSelector, \
    RoundRobinSelector
from .serializer import JSONSerializer
from .connection import Connection, RequestsHttpConnection, \
    Urllib3HttpConnection
from .exceptions import *

