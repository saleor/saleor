from ....page import models


def resolve_all_pages():
    return models.Page.objects.all().distinct()
