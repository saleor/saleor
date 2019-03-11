from textwrap import dedent

import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay

from ...discount import models
from ..core.connection import CountableDjangoObjectType
from ..core.fields import PrefetchingConnectionField
from ..core.types import CountryDisplay
from ..product.types import Category, Collection, Product
from ..translations.enums import LanguageCodeEnum
from ..translations.resolvers import resolve_translation
from ..translations.types import VoucherTranslation


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
        return self.collections.visible_to_user(info.context.user)

    def resolve_products(self, info, **kwargs):
        return self.products.visible_to_user(info.context.user)


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
    countries = graphene.List(
        CountryDisplay,
        description='List of countries available for the shipping voucher.')
    translation = graphene.Field(
        VoucherTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description='A language code to return the translation for.',
            required=True),
        description=(
            'Returns translated Voucher fields for the given language code.'),
        resolver=resolve_translation)

    class Meta:
        description = dedent("""
        Vouchers allow giving discounts to particular customers on categories,
        collections or specific products. They can be used during checkout by
        providing valid voucher codes.""")
        exclude_fields = ['translations']
        interfaces = [relay.Node]
        model = models.Voucher

    def resolve_categories(self, info, **kwargs):
        return self.categories.all()

    def resolve_collections(self, info, **kwargs):
        return self.collections.visible_to_user(info.context.user)

    def resolve_products(self, info, **kwargs):
        return self.products.visible_to_user(info.context.user)

    def resolve_countries(self, info, **kwargs):
        return [
            CountryDisplay(code=country.code, country=country.name)
            for country in self.countries]
