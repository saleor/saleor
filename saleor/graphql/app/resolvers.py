from ...app import models


def resolve_apps(info, **_kwargs):
    return models.App.objects.all()
