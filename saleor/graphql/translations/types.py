import graphene
from django.conf import settings

from ...discount import models as discount_models
from ...menu import models as menu_models
from ...page import models as page_models
from ...product import models as product_models
from ...shipping import models as shipping_models
from ...site import models as site_models
from ..core.connection import CountableDjangoObjectType
from ..core.utils import str_to_enum
from ..core.types import LanguageDisplay
from .enums import LanguageCodeEnum


class BaseTranslationType(CountableDjangoObjectType):
    language = graphene.Field(
        LanguageDisplay, description='Translation\'s language', required=True)

    class Meta:
        abstract = True

    def resolve_language(self, info):
        try:
            language = next(
                language[1] for language in settings.LANGUAGES
                if language[0] == self.language_code)
        except StopIteration:
            return None
        return LanguageDisplay(code=LanguageCodeEnum[str_to_enum(self.language_code)], language=language)


class AttributeValueTranslation(BaseTranslationType):
    class Meta:
        model = product_models.AttributeValueTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['attribute_value', 'language_code']


class AttributeTranslation(BaseTranslationType):
    class Meta:
        model = product_models.AttributeTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['attribute', 'language_code']


class ProductVariantTranslation(BaseTranslationType):
    class Meta:
        model = product_models.ProductVariantTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['product_variant', 'language_code']


class ProductTranslation(BaseTranslationType):
    class Meta:
        model = product_models.ProductTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['product', 'language_code']


class CollectionTranslation(BaseTranslationType):
    class Meta:
        model = product_models.CollectionTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['collection', 'language_code']


class CategoryTranslation(BaseTranslationType):
    class Meta:
        model = product_models.CategoryTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['category', 'language_code']


class PageTranslation(BaseTranslationType):
    class Meta:
        model = page_models.PageTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['page', 'language_code']


class VoucherTranslation(BaseTranslationType):
    class Meta:
        model = discount_models.VoucherTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['voucher', 'language_code']


class ShopTranslation(BaseTranslationType):
    class Meta:
        model = site_models.SiteSettingsTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['site_settings', 'language_code']


class MenuItemTranslation(BaseTranslationType):
    class Meta:
        model = menu_models.MenuItemTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['menu_item', 'language_code']


class ShippingMethodTranslation(BaseTranslationType):
    class Meta:
        model = shipping_models.ShippingMethodTranslation
        interfaces = [graphene.relay.Node]
        exclude_fields = ['shipping_method', 'language_code']
