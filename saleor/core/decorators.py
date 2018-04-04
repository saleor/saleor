from functools import wraps

from django.http import HttpResponseNotAllowed


def methods_required(*allowed_methods):
    def _decorator(view):
        @wraps(view)
        def _decorated_view(request, *args, **kwargs):
            if request.method not in allowed_methods:
                return HttpResponseNotAllowed(allowed_methods)
            return view(request, *args, **kwargs)
        return _decorated_view
    return _decorator


def requires_post_method():
    return methods_required('POST')
