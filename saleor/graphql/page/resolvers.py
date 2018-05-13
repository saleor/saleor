from ...page import models


def resolve_pages(user):
    if user.is_authenticated and user.is_active and user.is_staff:
        return models.Page.objects.all().distinct()
    return models.Page.objects.public().distinct()
