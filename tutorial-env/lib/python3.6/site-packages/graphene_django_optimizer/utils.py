noop = lambda *args, **kwargs: None


def is_iterable(obj):
    return hasattr(obj, '__iter__') and not isinstance(obj, str)
