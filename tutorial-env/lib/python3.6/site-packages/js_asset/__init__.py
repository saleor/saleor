from __future__ import absolute_import, unicode_literals


VERSION = (1, 2, 2)
__version__ = ".".join(map(str, VERSION))


try:
    from js_asset.js import *  # noqa
except ImportError:  # pragma: no cover
    pass
