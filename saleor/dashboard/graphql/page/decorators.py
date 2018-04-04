from functools import wraps

from graphql_jwt.exceptions import PermissionDenied

from ....page.models import Page


def must_be_unprotected(fn):
    """This decorator checks if the passed instance is not protected.

    If the instance is existing and is protected,
    it raises a `PermissionDenied`.

    If the instance is None (non existing) or non-protected,
    it will call the wrapped Mutator function,
    and pass the instance as a keyword parameter.
    """
    @wraps(fn)
    def wrapper(cls, instance: Page=None, *args, **kwargs):
        if instance and instance.is_protected:
            raise PermissionDenied()
        return fn(cls, *args, instance=instance, **kwargs)
    return wrapper
