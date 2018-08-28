from ...site import models

def resolve_site_settings_list():
    return models.SiteSettings.objects.all().distinct()
