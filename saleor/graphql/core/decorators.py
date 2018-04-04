from functools import wraps

from django.core.exceptions import PermissionDenied


def permission_required(*permissions):
    def decorator(func):
        @wraps(func)
        def wrapped_resolver(obj, info, *args, **kwargs):
            user_permissions = info.context.user.get_all_permissions()
            for permission in permissions:
                if permission not in user_permissions:
                    return PermissionDenied(
                        'You have no permission to view %s' % info.field_name)
            return func(obj, info, *args, **kwargs)
        return wrapped_resolver
    return decorator
