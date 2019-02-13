from .models import Page


def pages_visible_to_user(user):
    qs = Page.objects.prefetch_related('translations')
    if user.is_authenticated and user.is_active and user.is_staff:
        return qs
    return qs.published()
