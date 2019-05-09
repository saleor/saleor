import sys
# flake8: noqa


def import_attribute(import_path, exception_handler=None):
    try:
        from importlib import import_module
    except ImportError:  # pragma: no cover
        from django.utils.importlib import import_module
    module_name, object_name = import_path.rsplit('.', 1)
    try:
        module = import_module(module_name)
    except:  # pragma: no cover
        if callable(exception_handler):
            exctype, excvalue, tb = sys.exc_info()
            return exception_handler(import_path, exctype, excvalue, tb)
        else:
            raise
    try:
        return getattr(module, object_name)
    except:  # pragma: no cover
        if callable(exception_handler):
            exctype, excvalue, tb = sys.exc_info()
            return exception_handler(import_path, exctype, excvalue, tb)
        else:
            raise
