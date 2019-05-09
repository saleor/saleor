import warnings


class generic_deprecation(object):
    def __init__(
            self, message, warning_class=DeprecationWarning, stack_level=2):
        self.message = message
        self.warning_class = warning_class
        self.stack_level = stack_level

    def __call__(self, method):
        def wrapped(*args, **kwargs):
            warnings.warn(self.message, self.warning_class, self.stack_level)
            return method(*args, **kwargs)
        return wrapped
