from functools import wraps

import six
from graphql_jwt import exceptions
from graphql_jwt.decorators import context


def user_passes_test(test_func):
    def decorator(f):
        @wraps(f)
        @context(f)
        def wrapper(context, *args, **kwargs):
            if test_func(context):
                return f(*args, **kwargs)
            raise exceptions.PermissionDenied()

        return wrapper

    return decorator


def permission_required(perm):
    def check_perms(context):
        if isinstance(perm, six.string_types):
            perms = (perm,)
        else:
            perms = perm
        if context.user.has_perms(perms):
            return True
        bot = getattr(context, "bot", None)
        if bot and bot.has_perms(perms):
            return True
        return False

    return user_passes_test(check_perms)
