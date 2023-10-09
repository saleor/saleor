import graphene

from ..core.types import BaseObjectType
from ...pharmacy import models


class SiteSettingsType(BaseObjectType):
    class Meta:
        model = models.SiteSettings


class SiteSettingsList(BaseObjectType):
    edge = graphene.List(SiteSettingsType)
