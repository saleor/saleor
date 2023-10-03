from graphene_django.types import DjangoObjectType
from ...pharmacy import models


class SiteSettingsType(DjangoObjectType):
    class Meta:
        model = models.SiteSettings
