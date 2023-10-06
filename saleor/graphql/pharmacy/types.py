import graphene
from django.db.models import QuerySet
from graphene_django.types import DjangoObjectType

from ..core.types import ModelObjectType
from ...pharmacy import models


class SiteSettingsType(DjangoObjectType):
    class Meta:
        model = models.SiteSettings


class SiteSettingsList(graphene.ObjectType):
    edge = graphene.List(SiteSettingsType)
