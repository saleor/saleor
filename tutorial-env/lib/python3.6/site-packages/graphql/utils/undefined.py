class _Undefined(object):
    """A representation of an Undefined value distinct from a None value"""

    def __bool__(self):
        # type: () -> bool
        return False

    __nonzero__ = __bool__

    def __repr__(self):
        # type: () -> str
        return "Undefined"


Undefined = _Undefined()
