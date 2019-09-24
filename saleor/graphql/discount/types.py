import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay

from ...discount import models
from ..core import types
from ..core.connection import CountableDjangoObjectType
from ..core.fields import PrefetchingConnectionField
from ..product.types import Category, Collection, Product
from ..translations.enums import LanguageCodeEnum
from ..translations.resolvers import resolve_translation
from ..translations.types import SaleTranslation, VoucherTranslation
from .enums import DiscountValueTypeEnum, VoucherTypeEnum


class Sale(CountableDjangoObjectType):
    categories = gql_optimizer.field(
        PrefetchingConnectionField(
            Category, description="List of categories this sale applies to."
        ),
        model_field="categories",
    )
    collections = gql_optimizer.field(
        PrefetchingConnectionField(
            Collection, description="List of collections this sale applies to."
        ),
        model_field="collections",
    )
    products = gql_optimizer.field(
        PrefetchingConnectionField(
            Product, description="List of products this sale applies to."
        ),
        model_field="products",
    )
    translation = graphene.Field(
        SaleTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
            required=True,
        ),
        description="Returns translated sale fields for the given language code.",
        resolver=resolve_translation,
    )

    class Meta:
        description = """
        Sales allow creating discounts for categories, collections or
        products and are visible to all the customers."""
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
    categories = gql_optimizer.field(
        PrefetchingConnectionField(
            Category, description="List of categories this voucher applies to."
        ),
        model_field="categories",
    )
    collections = gql_optimizer.field(
        PrefetchingConnectionField(
            Collection, description="List of collections this voucher applies to."
        ),
        model_field="collections",
    )
    products = gql_optimizer.field(
        PrefetchingConnectionField(
            Product, description="List of products this voucher applies to."
        ),
        model_field="products",
    )
    countries = graphene.List(
        types.CountryDisplay,
        description="List of countries available for the shipping voucher.",
    )
    translation = graphene.Field(
        VoucherTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
            required=True,
        ),
        description="Returns translated Voucher fields for the given language code.",
        resolver=resolve_translation,
    )
    discount_value_type = DiscountValueTypeEnum(
        description="Determines a type of discount for voucher - value or percentage",
        required=True,
    )
    type = VoucherTypeEnum(description="Determines a type of voucher", required=True)
    min_amount_spent = graphene.Field(
        types.Money,
        deprecation_reason=(
            "DEPRECATED: Will be removed in Saleor 2.10, "
            "use the minSpent field instead."
        ),
    )

    class Meta:
        description = """
        Vouchers allow giving discounts to particular customers on categories,
        collections or specific products. They can be used during checkout by
        providing valid voucher codes."""
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

    @staticmethod
    def resolve_min_amount_spent(root: models.Voucher, *_args, **_kwargs):
        return root.min_spent
