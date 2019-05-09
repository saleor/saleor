try:
    from inspect import getfullargspec as _getargspec
except ImportError:
    from inspect import getargspec as _getargspec


class getargspec(object):
    def __init__(self, method):
        self.argspec = _getargspec(method)

    @property
    def args(self):
        return self.argspec.args

    @property
    def varargs(self):
        return self.argspec.varargs

    @property
    def varkw(self):
        if hasattr(self.argspec, 'keywords'):
            return self.argspec.keywords
        return self.argspec.varkw

    @property
    def defaults(self):
        return self.argspec.defaults
