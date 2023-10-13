from .utils import build_file_uri
from ...pharmacy import models


def resolve_all_site_settings():
    entities = models.SiteSettings.objects.all()
    for entity in entities:
        entity.image = build_file_uri(str(entity.image))
        entity.css = build_file_uri(str(entity.css))
    return entities


def resolve_site_settings_by_slug(slug):
    entity = models.SiteSettings.objects.filter(slug=slug).first()
    entity.image = build_file_uri(str(entity.image))
    entity.css = build_file_uri(str(entity.css))
    return entity
