from functools import wraps

from .deprecated import deprecated


@deprecated("This function is deprecated")
def resolve_only_args(func):
    @wraps(func)
    def wrapped_func(root, info, **args):
        return func(root, **args)

    return wrapped_func
