# coding=utf-8


def is_string(var):
    try:
        return isinstance(var, basestring)
    except NameError:
        return isinstance(var, str)


def quote(var):
    return ('"{0}"' if '"' not in var else "'{0}'").format(var)
