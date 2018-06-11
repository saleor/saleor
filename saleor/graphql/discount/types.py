from graphene import relay

from ...discount import models
from ..core.types import CountableDjangoObjectType


class Voucher(CountableDjangoObjectType):
    class Meta:
        description = """A token that can be used to purchase products
        for discounted price."""
        interfaces = [relay.Node]
        filter_fields = {
            'name': ['icontains'],
            'type': ['exact'],
            'discount_value': ['gte', 'lte'],
            'start_date': ['exact'],
            'end_date': ['exact'],
            'limit': ['gte', 'lte']}
        model = models.Voucher


class Sale(CountableDjangoObjectType):
    class Meta:
        description = """A special event featuring discounts
        for selected products"""
        interfaces = [relay.Node]
        filter_fields = {
            'name': ['icontains'],
            'type': ['icontains'],
            'value': ['gte', 'lte']}
        model = models.Sale
