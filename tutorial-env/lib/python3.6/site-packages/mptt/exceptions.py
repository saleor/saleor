"""
MPTT exceptions.
"""


class InvalidMove(Exception):
    """
    An invalid node move was attempted.

    For example, attempting to make a node a child of itself.
    """
    pass


class CantDisableUpdates(Exception):
    """
    User tried to disable updates on a model that doesn't support it
    (abstract, proxy or a multiple-inheritance subclass of an MPTTModel)
    """
    pass
