import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Model
from graphql import GraphQLError

from ...attribute import models as attribute_models
from ...core.permissions import SitePermissions
from ...core.tracing import traced_atomic_transaction
from ...discount import models as discount_models
from ...menu import models as menu_models
from ...page import models as page_models
from ...product import models as product_models
from ...shipping import models as shipping_models
from ...site.models import SiteSettings
from ..attribute.types import Attribute, AttributeValue
from ..channel import ChannelContext
from ..core.descriptions import RICH_CONTENT
from ..core.enums import LanguageCodeEnum, TranslationErrorCode
from ..core.fields import JSONString
from ..core.mutations import BaseMutation, ModelMutation
from ..core.types import TranslationError
from ..core.utils import from_global_id_or_error
from ..discount.types import Sale, Voucher
from ..menu.types import MenuItem
from ..product.types import Category, Collection, Product, ProductVariant
from ..shipping.types import ShippingMethodType
from ..shop.types import Shop
from . import types as translation_types

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
    # Page Translation mutation reverses model and TranslatableContent
    page_models.Page._meta.object_name: str(translation_types.PageTranslatableContent),
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


def validate_input_against_model(model: Model, input_data: dict):
    data_to_validate = {key: value for key, value in input_data.items() if value}
    instance = model(**data_to_validate)  # type: ignore
    all_fields = [field.name for field in model._meta.fields]
    exclude_fields = set(all_fields) - set(data_to_validate)
    instance.full_clean(exclude=exclude_fields, validate_unique=False)


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
        try:
            node_type, node_pk = from_global_id_or_error(node_id)
        except GraphQLError:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Invalid ID has been provided.",
                        code=TranslationErrorCode.INVALID,
                    )
                }
            )

        # This mutation accepts either model IDs or translatable content IDs. Below we
        # check if provided ID refers to a translatable content which matches with the
        # expected model_type. If so, we transform the translatable content ID to model
        # ID.
        tc_model_type = TRANSLATABLE_CONTENT_TO_MODEL.get(node_type)

        if tc_model_type and tc_model_type == str(cls._meta.object_type):
            node_id = graphene.Node.to_global_id(tc_model_type, node_pk)

        return node_id, cls._meta.object_type

    @classmethod
    def validate_input(cls, input_data):
        validate_input_against_model(cls._meta.model, input_data)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id, model_type = cls.clean_node_id(**data)
        instance = cls.get_node_or_error(info, node_id, only_type=model_type)
        cls.validate_input(data["input"])

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
    rich_text = JSONString(description="Translated text." + RICH_CONTENT)
    plain_text = graphene.String(description="Translated text.")


class SeoTranslationInput(graphene.InputObjectType):
    seo_title = graphene.String()
    seo_description = graphene.String()


class TranslationInput(NameTranslationInput, SeoTranslationInput):
    description = JSONString(description="Translated description." + RICH_CONTENT)


class ShippingPriceTranslationInput(NameTranslationInput):
    description = JSONString(
        description="Translated shipping method description." + RICH_CONTENT
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
        object_type = Category
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
        object_type = Product
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        node_id = cls.clean_node_id(**data)[0]
        product = cls.get_node_or_error(info, node_id, only_type=Product)
        cls.validate_input(data["input"])

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
        object_type = Collection
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
        object_type = ProductVariant
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
        cls.validate_input(data["input"])
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
        object_type = Attribute
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
        object_type = AttributeValue
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
        object_type = Sale
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
        object_type = Voucher
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
            description=(
                "ShippingMethodType ID or ShippingMethodTranslatableContent ID."
            ),
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = ShippingPriceTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for a shipping method."
        model = shipping_models.ShippingMethod
        object_type = ShippingMethodType
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = ChannelContext(node=response.shippingMethod, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})

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
        object_type = MenuItem
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
    content = JSONString(description="Translated page content." + RICH_CONTENT)


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
        # Note: `PageTranslate` is only mutation that returns "TranslatableContent"
        object_type = translation_types.PageTranslatableContent
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
            description="Fields required to update shop settings translations.",
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
        validate_input_against_model(SiteSettings, data["input"])
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
