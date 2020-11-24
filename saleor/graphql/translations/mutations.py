import graphene
from django.core.exceptions import ValidationError

from ...attribute import models as attribute_models
from ...core.permissions import SitePermissions
from ...discount import models as discount_models
from ...menu import models as menu_models
from ...page import models as page_models
from ...product import models as product_models
from ...shipping import models as shipping_models
from ..channel import ChannelContext
from ..core.mutations import BaseMutation, ModelMutation, registry
from ..core.types.common import TranslationError
from ..core.utils import from_global_id_strict_type
from ..product.types import Product, ProductVariant
from ..shop.types import Shop
from .enums import LanguageCodeEnum

# discount types need to be imported to get Voucher in the graphene registry
from ..discount import types  # noqa # pylint: disable=unused-import, isort:skip


class BaseTranslateMutation(ModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, context):
        return context.user.has_perm(SitePermissions.MANAGE_TRANSLATIONS)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if "id" in data and not data["id"]:
            raise ValidationError(
                {"id": ValidationError("This field is required", code="required")}
            )

        model_type = registry.get_type_for_model(cls._meta.model)
        instance = cls.get_node_or_error(info, data["id"], only_type=model_type)
        instance.translations.update_or_create(
            language_code=data["language_code"], defaults=data["input"]
        )
        return cls(**{cls._meta.return_field_name: instance})


class NameTranslationInput(graphene.InputObjectType):
    name = graphene.String()


class SeoTranslationInput(graphene.InputObjectType):
    seo_title = graphene.String()
    seo_description = graphene.String()


class TranslationInput(NameTranslationInput, SeoTranslationInput):
    description = graphene.String()
    description_json = graphene.JSONString()


class CategoryTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Category ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = TranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for Category."
        model = product_models.Category
        error_type_class = TranslationError
        error_type_field = "translation_errors"


class ProductTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Product ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = TranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for Product."
        model = product_models.Product
        error_type_class = TranslationError
        error_type_field = "translation_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if "id" in data and not data["id"]:
            raise ValidationError(
                {"id": ValidationError("This field is required", code="required")}
            )

        product_pk = from_global_id_strict_type(data["id"], Product, field="id")
        product = product_models.Product.objects.get(pk=product_pk)
        product.translations.update_or_create(
            language_code=data["language_code"], defaults=data["input"]
        )
        product = ChannelContext(node=product, channel_slug=None)
        return cls(**{cls._meta.return_field_name: product})


class CollectionTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Collection ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = TranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for collection."
        model = product_models.Collection
        error_type_class = TranslationError
        error_type_field = "translation_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.collection, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})


class ProductVariantTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Product Variant ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for Product Variant."
        model = product_models.ProductVariant
        error_type_class = TranslationError
        error_type_field = "translation_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if "id" in data and not data["id"]:
            raise ValidationError(
                {"id": ValidationError("This field is required", code="required")}
            )

        variant_pk = from_global_id_strict_type(data["id"], ProductVariant, field="id")
        variant = product_models.ProductVariant.objects.get(pk=variant_pk)
        variant.translations.update_or_create(
            language_code=data["language_code"], defaults=data["input"]
        )
        variant = ChannelContext(node=variant, channel_slug=None)
        return cls(**{cls._meta.return_field_name: variant})


class AttributeTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Attribute ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for attribute."
        model = attribute_models.Attribute
        error_type_class = TranslationError
        error_type_field = "translation_errors"


class AttributeValueTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Attribute Value ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for attribute value."
        model = attribute_models.AttributeValue
        error_type_class = TranslationError
        error_type_field = "translation_errors"


class SaleTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Voucher ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a sale."
        model = discount_models.Sale
        error_type_class = TranslationError
        error_type_field = "translation_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.sale, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})


class VoucherTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Voucher ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for Voucher."
        model = discount_models.Voucher
        error_type_class = TranslationError
        error_type_field = "translation_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.voucher, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})


class ShippingPriceTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Shipping method ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for shipping method."
        model = shipping_models.ShippingMethod
        error_type_class = TranslationError
        error_type_field = "translation_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.shippingMethod, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})


class MenuItemTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Menu Item ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for Menu Item."
        model = menu_models.MenuItem
        error_type_class = TranslationError
        error_type_field = "translation_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.menuItem, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})


class PageTranslationInput(SeoTranslationInput):
    title = graphene.String()
    content = graphene.String()
    content_json = graphene.JSONString()


class PageTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description="Page ID.")
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = PageTranslationInput(required=True)

    class Meta:
        description = "Creates/Updates translations for Page."
        model = page_models.Page
        error_type_class = TranslationError
        error_type_field = "translation_errors"


class ShopSettingsTranslationInput(graphene.InputObjectType):
    header_text = graphene.String()
    description = graphene.String()


class ShopSettingsTranslate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = ShopSettingsTranslationInput(
            description=("Fields required to update shop settings translations."),
            required=True,
        )

    class Meta:
        description = "Creates/Updates translations for Shop Settings."
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)
        error_type_class = TranslationError
        error_type_field = "translation_errors"

    @classmethod
    def perform_mutation(cls, _root, info, language_code, **data):
        instance = info.context.site.settings
        instance.translations.update_or_create(
            language_code=language_code, defaults=data.get("input")
        )
        return ShopSettingsTranslate(shop=Shop())
