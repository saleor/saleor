from textwrap import dedent

from graphene import relay

from ...page import models
from ..core.types.common import CountableDjangoObjectType


class Page(CountableDjangoObjectType):
    class Meta:
        description = dedent("""A static page that can be manually added by a shop
        operator through the dashboard.""")
        exclude_fields = ['voucher_set', 'sale_set', 'menuitem_set']
        interfaces = [relay.Node]
        model = models.Page
