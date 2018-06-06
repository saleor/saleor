from graphene import relay

from ...discount import models
from ..core.types import CountableDjangoObjectType


class Voucher(CountableDjangoObjectType):
    class Meta:
        description = """A token that can be used to purchase products
        for discounted price."""
        interfaces = [relay.Node]
        filter_fields = [
            'name', 'type', 'discount_value', 'start_date', 'end_date']
        model = models.Voucher
