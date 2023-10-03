from ...pharmacy import models


def resolve_all_site_settings():
    return models.SiteSettings.objects.all()


def resolve_site_settings_by_slug(slug):
    return models.SiteSettings.objects.filter(slug=slug).first()
