import graphene
from graphene import relay

from ...site import models
from ..core.types.common import CountableDjangoObjectType


class SiteSettings(CountableDjangoObjectType):
    domain = graphene.String()

    class Meta:
        model = models.SiteSettings
        interfaces = [relay.Node]

    def resolve_domain(self, info):
        return self.site.domain
