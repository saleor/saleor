import graphene
from graphene import relay

from ...discount import models
from ..core import types
from ..core.connection import CountableDjangoObjectType
from ..core.fields import PrefetchingConnectionField
from ..product.types import Category, Collection, Product
from ..translations.fields import TranslationField
from ..translations.types import SaleTranslation, VoucherTranslation
from .enums import DiscountValueTypeEnum, VoucherTypeEnum


class Sale(CountableDjangoObjectType):
    categories = PrefetchingConnectionField(
        Category, description="List of categories this sale applies to."
    )
    collections = PrefetchingConnectionField(
        Collection, description="List of collections this sale applies to."
    )
    products = PrefetchingConnectionField(
        Product, description="List of products this sale applies to."
    )
    translation = TranslationField(SaleTranslation, type_name="sale")

    class Meta:
        description = (
            "Sales allow creating discounts for categories, collections or products "
            "and are visible to all the customers."
        )
        interfaces = [relay.Node]
        model = models.Sale
        only_fields = ["end_date", "id", "name", "start_date", "type", "value"]

    @staticmethod
    def resolve_categories(root: models.Sale, *_args, **_kwargs):
        return root.categories.all()

    @staticmethod
    def resolve_collections(root: models.Sale, info, **_kwargs):
        return root.collections.visible_to_user(info.context.user)

    @staticmethod
    def resolve_products(root: models.Sale, info, **_kwargs):
        return root.products.visible_to_user(info.context.user)


class Voucher(CountableDjangoObjectType):
    categories = PrefetchingConnectionField(
        Category, description="List of categories this voucher applies to."
    )
    collections = PrefetchingConnectionField(
        Collection, description="List of collections this voucher applies to."
    )
    products = PrefetchingConnectionField(
        Product, description="List of products this voucher applies to."
    )
    countries = graphene.List(
        types.CountryDisplay,
        description="List of countries available for the shipping voucher.",
    )
    translation = TranslationField(VoucherTranslation, type_name="voucher")
    discount_value_type = DiscountValueTypeEnum(
        description="Determines a type of discount for voucher - value or percentage",
        required=True,
    )
    type = VoucherTypeEnum(description="Determines a type of voucher.", required=True)

    class Meta:
        description = (
            "Vouchers allow giving discounts to particular customers on categories, "
            "collections or specific products. They can be used during checkout by "
            "providing valid voucher codes."
        )
        only_fields = [
            "apply_once_per_order",
            "apply_once_per_customer",
            "code",
            "discount_value",
            "discount_value_type",
            "end_date",
            "id",
            "min_spent",
            "min_checkout_items_quantity",
            "name",
            "start_date",
            "type",
            "usage_limit",
            "used",
        ]
        interfaces = [relay.Node]
        model = models.Voucher

    @staticmethod
    def resolve_categories(root: models.Voucher, *_args, **_kwargs):
        return root.categories.all()

    @staticmethod
    def resolve_collections(root: models.Voucher, info, **_kwargs):
        return root.collections.visible_to_user(info.context.user)

    @staticmethod
    def resolve_products(root: models.Voucher, info, **_kwargs):
        return root.products.visible_to_user(info.context.user)

    @staticmethod
    def resolve_countries(root: models.Voucher, *_args, **_kwargs):
        return [
            types.CountryDisplay(code=country.code, country=country.name)
            for country in root.countries
        ]
