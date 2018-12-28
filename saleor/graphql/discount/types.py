from textwrap import dedent

import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay

from ...discount import DiscountValueType, VoucherType, models
from ..core.connection import CountableDjangoObjectType
from ..core.fields import PrefetchingConnectionField
from ..product.types import Category, Collection, Product


class Voucher(CountableDjangoObjectType):
    categories = gql_optimizer.field(
        PrefetchingConnectionField(
            Category,
            description='List of categories this voucher applies to.'),
        model_field='categories')
    collections = gql_optimizer.field(
        PrefetchingConnectionField(
            Collection,
            description='List of collections this voucher applies to.'),
        model_field='collections')
    products = gql_optimizer.field(
        PrefetchingConnectionField(
            Product,
            description='List of products this voucher applies to.'),
        model_field='products')

    class Meta:
        description = dedent("""
        Vouchers allow giving discounts to particular customers on categories,
        collections or specific products. They can be used during checkout by
        providing valid voucher codes.""")
        interfaces = [relay.Node]
        model = models.Voucher

    def resolve_categories(self, info, **kwargs):
        return self.categories.all()

    def resolve_collections(self, info, **kwargs):
        return self.collections.all()

    def resolve_products(self, info, **kwargs):
        return self.products.all()


class Sale(CountableDjangoObjectType):
    categories = gql_optimizer.field(
        PrefetchingConnectionField(
            Category,
            description='List of categories this sale applies to.'),
        model_field='categories')
    collections = gql_optimizer.field(
        PrefetchingConnectionField(
            Collection,
            description='List of collections this sale applies to.'),
        model_field='collections')
    products = gql_optimizer.field(
        PrefetchingConnectionField(
            Product,
            description='List of products this sale applies to.'),
        model_field='products')

    class Meta:
        description = dedent("""
        Sales allow creating discounts for categories, collections or
        products and are visible to all the customers.""")
        interfaces = [relay.Node]
        model = models.Sale

    def resolve_categories(self, info, **kwargs):
        return self.categories.all()

    def resolve_collections(self, info, **kwargs):
        return self.collections.all()

    def resolve_products(self, info, **kwargs):
        return self.products.all()


class VoucherTypeEnum(graphene.Enum):
    PRODUCT = VoucherType.PRODUCT
    COLLECTION = VoucherType.COLLECTION
    CATEGORY = VoucherType.CATEGORY
    SHIPPING = VoucherType.SHIPPING
    VALUE = VoucherType.VALUE


class DiscountValueTypeEnum(graphene.Enum):
    FIXED = DiscountValueType.FIXED
    PERCENTAGE = DiscountValueType.PERCENTAGE
