__version__ = "0.10.0"
VERSION = tuple(__version__.split("."))

default_app_config = "mptt.apps.MpttConfig"


def register(*args, **kwargs):
    """
    Registers a model class as an MPTTModel, adding MPTT fields and adding MPTTModel to __bases__.
    This is equivalent to just subclassing MPTTModel, but works for an already-created model.
    """
    from mptt.models import MPTTModelBase
    return MPTTModelBase.register(*args, **kwargs)


class AlreadyRegistered(Exception):
    "Deprecated - don't use this anymore. It's never thrown, you don't need to catch it"
