import functools

from django.http import Http404


def require_show_toolbar(view):
    @functools.wraps(view)
    def inner(request, *args, **kwargs):
        from debug_toolbar.middleware import get_show_toolbar

        show_toolbar = get_show_toolbar()
        if not show_toolbar(request):
            raise Http404

        return view(request, *args, **kwargs)

    return inner
