import graphene
from django.conf import settings

from ...discount import models as discount_models
from ...menu import models as menu_models
from ...page import models as page_models
from ...product import models as product_models
from ...shipping import models as shipping_models
from ...site import models as site_models
from ..core.connection import CountableDjangoObjectType
from ..core.types import LanguageDisplay
from ..core.utils import str_to_enum
from .enums import LanguageCodeEnum
from .resolvers import resolve_translation


class BaseTranslationType(CountableDjangoObjectType):
    language = graphene.Field(
        LanguageDisplay, description="Translation language.", required=True
    )

    class Meta:
        abstract = True

    @staticmethod
    def resolve_language(root, *_args):
        try:
            language = next(
                language[1]
                for language in settings.LANGUAGES
                if language[0] == root.language_code
            )
        except StopIteration:
            return None
        return LanguageDisplay(
            code=LanguageCodeEnum[str_to_enum(root.language_code)], language=language
        )


class AttributeValueTranslation(BaseTranslationType):
    class Meta:
        model = product_models.AttributeValueTranslation
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "name"]


class AttributeTranslation(BaseTranslationType):
    class Meta:
        model = product_models.AttributeTranslation
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "name"]


class ProductVariantTranslation(BaseTranslationType):
    class Meta:
        model = product_models.ProductVariantTranslation
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "name"]


class ProductTranslation(BaseTranslationType):
    class Meta:
        model = product_models.ProductTranslation
        interfaces = [graphene.relay.Node]
        only_fields = [
            "description",
            "description_json",
            "id",
            "name",
            "seo_title",
            "seo_description",
        ]


class ProductStrings(CountableDjangoObjectType):
    translation = graphene.Field(
        ProductTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
            required=True,
        ),
        description=("Returns translated Product fields for the given language code."),
        resolver=resolve_translation,
    )
    product = graphene.Field(
        "saleor.graphql.product.types.products.Product",
        description="Represents an individual item for sale in the storefront.",
    )

    class Meta:
        model = product_models.Product
        interfaces = [graphene.relay.Node]
        only_fields = [
            "description",
            "description_json",
            "id",
            "name",
            "seo_title",
            "seo_description",
        ]

    def resolve_product(self, info):
        return (
            product_models.Product.objects.visible_to_user(info.context.user)
            .filter(pk=self.id)
            .first()
        )


class CollectionTranslation(BaseTranslationType):
    class Meta:
        model = product_models.CollectionTranslation
        interfaces = [graphene.relay.Node]
        only_fields = [
            "description",
            "description_json",
            "id",
            "name",
            "seo_title",
            "seo_description",
        ]


class CollectionStrings(CountableDjangoObjectType):
    translation = graphene.Field(
        CollectionTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
            required=True,
        ),
        description=(
            "Returns translated Collection fields " "for the given language code."
        ),
        resolver=resolve_translation,
    )
    collection = graphene.Field(
        "saleor.graphql.product.types.products.Collection",
        description="Represents a collection of products.",
    )

    class Meta:
        model = product_models.Collection
        interfaces = [graphene.relay.Node]
        only_fields = [
            "description",
            "description_json",
            "id",
            "name",
            "seo_title",
            "seo_description",
        ]

    def resolve_collection(self, info):
        return (
            product_models.Collection.objects.visible_to_user(info.context.user)
            .filter(pk=self.id)
            .first()
        )


class CategoryTranslation(BaseTranslationType):
    class Meta:
        model = product_models.CategoryTranslation
        interfaces = [graphene.relay.Node]
        only_fields = [
            "description",
            "description_json",
            "id",
            "name",
            "seo_title",
            "seo_description",
        ]


class CategoryStrings(CountableDjangoObjectType):
    translation = graphene.Field(
        CategoryTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
            required=True,
        ),
        description=("Returns translated Category fields for the given language code."),
        resolver=resolve_translation,
    )
    category = graphene.Field(
        "saleor.graphql.product.types.products.Category",
        description="Represents a single category of products.",
    )

    class Meta:
        model = product_models.Category
        interfaces = [graphene.relay.Node]
        only_fields = [
            "description",
            "description_json",
            "id",
            "name",
            "seo_title",
            "seo_description",
        ]

    def resolve_category(self, info):
        return self


class PageTranslation(BaseTranslationType):
    class Meta:
        model = page_models.PageTranslation
        interfaces = [graphene.relay.Node]
        only_fields = [
            "content",
            "content_json",
            "id",
            "seo_description",
            "seo_title",
            "title",
        ]


class VoucherTranslation(BaseTranslationType):
    class Meta:
        model = discount_models.VoucherTranslation
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "name"]


class SaleTranslation(BaseTranslationType):
    class Meta:
        model = discount_models.SaleTranslation
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "name"]


class ShopTranslation(BaseTranslationType):
    class Meta:
        model = site_models.SiteSettingsTranslation
        interfaces = [graphene.relay.Node]
        only_fields = ["description", "header_text", "id"]


class MenuItemTranslation(BaseTranslationType):
    class Meta:
        model = menu_models.MenuItemTranslation
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "name"]


class ShippingMethodTranslation(BaseTranslationType):
    class Meta:
        model = shipping_models.ShippingMethodTranslation
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "name"]
