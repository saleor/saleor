from ...app import models


def resolve_apps_installations(info, **_kwargs):
    return models.AppInstallation.objects.all()


def resolve_apps(info, **_kwargs):
    return models.App.objects.all()
