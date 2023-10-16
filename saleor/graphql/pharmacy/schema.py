import graphene

from ..core import ResolveInfo
from .types import SiteSettingsType, SiteSettingsList
from .mutations import SiteSettingsCreate, SiteSettingsUpdate, SiteSettingsDelete
from .resolvers import (
    resolve_site_settings_by_slug,
    resolve_all_site_settings
)
from ...permission.enums import SitePermissions
from ..core.fields import PermissionsField


class SiteSettingsQueries(graphene.ObjectType):
    site_settings = PermissionsField(
        SiteSettingsType,
        slug=graphene.String(),
        permissions=[
            SitePermissions.MANAGE_SETTINGS,
        ])
    all_site_settings = PermissionsField(
        SiteSettingsList,
        permissions=[
            SitePermissions.MANAGE_SETTINGS,
        ]
    )

    @staticmethod
    def resolve_site_settings(_root, _info: ResolveInfo, *, slug=None, **kwargs):
        if slug:
            return resolve_site_settings_by_slug(slug)

    @staticmethod
    def resolve_all_site_settings(_root, _info: ResolveInfo):
        site_settings_list = SiteSettingsList()
        all_site_settings = resolve_all_site_settings()
        site_settings_list.edge = all_site_settings
        return site_settings_list


class SiteSettingsMutations(graphene.ObjectType):
    site_settings_create = SiteSettingsCreate.Field()
    site_settings_update = SiteSettingsUpdate.Field()
    site_settings_delete = SiteSettingsDelete.Field()
