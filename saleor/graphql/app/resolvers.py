from ...app import models


def resolve_ongoing_apps_installations(info, **_kwargs):
    return models.AppJob.objects.all()


def resolve_apps(info, **_kwargs):
    return models.App.objects.all()
