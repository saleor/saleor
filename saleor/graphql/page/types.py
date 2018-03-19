from graphene import relay

from ...page import models
from ..core.types import CountableDjangoObjectType


class Page(CountableDjangoObjectType):
    class Meta:
        model = models.Page
        interfaces = [relay.Node]


def resolve_pages():
    return models.Page.objects.public().distinct()
