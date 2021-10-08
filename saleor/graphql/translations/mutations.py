import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ...attribute import models as attribute_models
from ...core.permissions import SitePermissions
from ...core.tracing import traced_atomic_transaction
from ...discount import models as discount_models
from ...menu import models as menu_models
from ...page import models as page_models
from ...product import models as product_models
from ...shipping import models as shipping_models
from ..channel import ChannelContext
from ..core.enums import LanguageCodeEnum
from ..core.mutations import BaseMutation, ModelMutation, registry
from ..core.types.common import TranslationError
from ..product.types import Product, ProductVariant
from ..shipping import types as shipping_types
from ..shop.types import Shop
from . import types as translation_types

# discount and menu types need to be imported to get
# Voucher and Menu in the graphene registry
from ..discount import types  # noqa # pylint: disable=unused-import, isort:skip
from ..menu import types  # type: ignore # noqa # pylint: disable=unused-import, isort:skip


TRANSLATABLE_CONTENT_TO_MODEL = {
    str(
        translation_types.ProductTranslatableContent
    ): product_models.Product._meta.object_name,
    str(
        translation_types.CollectionTranslatableContent
    ): product_models.Collection._meta.object_name,
    str(
        translation_types.CategoryTranslatableContent
    ): product_models.Category._meta.object_name,
    str(
        translation_types.AttributeTranslatableContent
    ): attribute_models.Attribute._meta.object_name,
    str(
        translation_types.AttributeValueTranslatableContent
    ): attribute_models.AttributeValue._meta.object_name,
    str(
        translation_types.ProductVariantTranslatableContent
    ): product_models.ProductVariant._meta.object_name,
    str(translation_types.PageTranslatableContent): page_models.Page._meta.object_name,
    str(
        translation_types.ShippingMethodTranslatableContent
    ): shipping_models.ShippingMethod._meta.object_name,
    str(
        translation_types.SaleTranslatableContent
    ): discount_models.Sale._meta.object_name,
    str(
        translation_types.VoucherTranslatableContent
    ): discount_models.Voucher._meta.object_name,
    str(
        translation_types.MenuItemTranslatableContent
    ): menu_models.MenuItem._meta.object_name,
}


class BaseTranslateMutation(ModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def clean_node_id(cls, **data):
        if "id" in data and not data["id"]:
            raise ValidationError(
                {"id": ValidationError("This field is required", code="required")}
            )

        node_id = data["id"]
        node_type, node_pk = graphene.Node.from_global_id(node_id)
        model_type = registry.get_type_for_model(cls._meta.model)

        # This mutation accepts either model IDs or translatable content IDs. Below we
        # check if provided ID refers to a translatable content which matches with the
        # expected model_type. If so, we transform the translatable content ID to model
        # ID.
        tc_model_type = TRANSLATABLE_CONTENT_TO_MODEL.get(node_type)
        if tc_model_type and tc_model_type == str(model_type):
            node_id = graphene.Node.to_global_id(tc_model_type, node_pk)

        return node_id, model_type

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id, model_type = cls.clean_node_id(**data)
        instance = cls.get_node_or_error(info, node_id, only_type=model_type)
        translation, created = instance.translations.update_or_create(
            language_code=data["language_code"], defaults=data["input"]
        )

        def on_commit():
            if created:
                info.context.plugins.translation_created(translation)
            else:
                info.context.plugins.translation_updated(translation)

        transaction.on_commit(on_commit)
        return cls(**{cls._meta.return_field_name: instance})


class NameTranslationInput(graphene.InputObjectType):
    name = graphene.String()


class AttributeValueTranslationInput(NameTranslationInput):
    rich_text = graphene.JSONString()


class SeoTranslationInput(graphene.InputObjectType):
    seo_title = graphene.String()
    seo_description = graphene.String()


class TranslationInput(NameTranslationInput, SeoTranslationInput):
    description = graphene.JSONString()


class ShippingPriceTranslationInput(NameTranslationInput):
    description = graphene.JSONString(
        description="Translated shipping method description (JSON)."
    )


class CategoryTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="Category ID or CategoryTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = TranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a category."
        model = product_models.Category
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)


class ProductTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="Product ID or ProductTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = TranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a product."
        model = product_models.Product
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        node_id = cls.clean_node_id(**data)[0]
        product = cls.get_node_or_error(info, node_id, only_type=Product)

        translation, created = product.translations.update_or_create(
            language_code=data["language_code"], defaults=data["input"]
        )
        product = ChannelContext(node=product, channel_slug=None)

        def on_commit():
            if created:
                info.context.plugins.translation_created(translation)
            else:
                info.context.plugins.translation_updated(translation)

        transaction.on_commit(on_commit)

        return cls(**{cls._meta.return_field_name: product})


class CollectionTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="Collection ID or CollectionTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = TranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a collection."
        model = product_models.Collection
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.collection, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})


class ProductVariantTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="ProductVariant ID or ProductVariantTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a product variant."
        model = product_models.ProductVariant
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        node_id = cls.clean_node_id(**data)[0]
        variant_pk = cls.get_global_id_or_error(node_id, only_type=ProductVariant)
        variant = product_models.ProductVariant.objects.prefetched_for_webhook().get(
            pk=variant_pk
        )
        translation, created = variant.translations.update_or_create(
            language_code=data["language_code"], defaults=data["input"]
        )
        variant = ChannelContext(node=variant, channel_slug=None)

        def on_commit():
            info.context.plugins.product_variant_updated(variant.node)

            if created:
                info.context.plugins.translation_created(translation)
            else:
                info.context.plugins.translation_updated(translation)

        transaction.on_commit(on_commit)

        return cls(**{cls._meta.return_field_name: variant})


class AttributeTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="Attribute ID or AttributeTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for an attribute."
        model = attribute_models.Attribute
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)


class AttributeValueTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="AttributeValue ID or AttributeValueTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = AttributeValueTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for an attribute value."
        model = attribute_models.AttributeValue
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)


class SaleTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="Sale ID or SaleTranslatableContent ID."
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a sale."
        model = discount_models.Sale
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.sale, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})


class VoucherTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="Voucher ID or VoucherTranslatableContent ID."
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a voucher."
        model = discount_models.Voucher
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.voucher, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})


class ShippingPriceTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="ShippingMethod ID or ShippingMethodTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = ShippingPriceTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a shipping method."
        model = shipping_models.ShippingMethod
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.shippingMethod, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})

    @classmethod
    def get_type_for_model(cls):
        return shipping_types.ShippingMethod

    @classmethod
    def get_node_or_error(cls, info, node_id, field="id", only_type=None, qs=None):
        return super().get_node_or_error(
            info, node_id, field, qs=shipping_models.ShippingMethod.objects
        )


class MenuItemTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="MenuItem ID or MenuItemTranslatableContent ID."
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a menu item."
        model = menu_models.MenuItem
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.menuItem, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})


class PageTranslationInput(SeoTranslationInput):
    title = graphene.String()
    content = graphene.JSONString()


class PageTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="Page ID or PageTranslatableContent ID."
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = PageTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a page."
        model = page_models.Page
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)


class ShopSettingsTranslationInput(graphene.InputObjectType):
    header_text = graphene.String()
    description = graphene.String()


class ShopSettingsTranslate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop settings.")

    class Arguments:
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = ShopSettingsTranslationInput(
            description=("Fields required to update shop settings translations."),
            required=True,
        )

    class Meta:
        description = "Creates/updates translations for shop settings."
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, language_code, **data):
        instance = info.context.site.settings
        translation, created = instance.translations.update_or_create(
            language_code=language_code, defaults=data.get("input")
        )

        def on_commit():
            if created:
                info.context.plugins.translation_created(translation)
            else:
                info.context.plugins.translation_updated(translation)

        transaction.on_commit(on_commit)

        return ShopSettingsTranslate(shop=Shop())
