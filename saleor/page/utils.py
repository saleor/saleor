from .models import Page


def pages_visible_to_user(user):
    if user.is_authenticated and user.is_active and user.is_staff:
        return Page.objects.all()
    return Page.objects.public()
