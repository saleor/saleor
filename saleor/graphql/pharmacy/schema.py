import graphene
from django.contrib.sites.models import Site

from ..core import ResolveInfo
from .types import SiteSettingsType
from .mutations import SiteSettingsCreate, SiteSettingsUpdate
from .resolvers import (
    resolve_site_settings_by_slug,
    resolve_all_site_settings
)
from ...pharmacy_settings import MEDIA_URL


class SiteSettingsQueries(graphene.ObjectType):
    site_settings = graphene.Field(SiteSettingsType, slug=graphene.String())
    all_site_settings = graphene.List(SiteSettingsType)

    @staticmethod
    def resolve_site_settings(_root, _info: ResolveInfo, *, slug=None, **kwargs):
        if slug:
            site_settings = resolve_site_settings_by_slug(slug)

            domain = Site.objects.get_current().domain
            site_settings.image = f"{domain}{MEDIA_URL}{site_settings.image}"
            site_settings.css = f"{domain}{MEDIA_URL}{site_settings.css}" \
                if site_settings.css else ""

            return site_settings

    @staticmethod
    def resolve_all_site_settings(_root, _info: ResolveInfo):
        all_site_settings = resolve_all_site_settings()

        domain = Site.objects.get_current().domain
        for site_settings in all_site_settings:
            site_settings.image = f"{domain}{MEDIA_URL}{site_settings.image}"
            site_settings.css = f"{domain}{MEDIA_URL}{site_settings.css}" \
                if site_settings.css else ""

        return all_site_settings


class SiteSettingsMutations(graphene.ObjectType):
    site_settings_create = SiteSettingsCreate.Field()
    site_settings_update = SiteSettingsUpdate.Field()
