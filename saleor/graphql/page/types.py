from graphene import relay

from ...page import models
from ..core.types import CountableDjangoObjectType


class Page(CountableDjangoObjectType):
    class Meta:
        model = models.Page
        interfaces = [relay.Node]


def resolve_pages(info):
    return models.Page.objects.public().distinct()


def resolve_all_pages(info):
    return models.Page.objects.all().distinct()
