import graphene
from graphql_jwt.decorators import permission_required
from graphql_jwt.exceptions import PermissionDenied

from ...discount import models as discount_models
from ...menu import models as menu_models
from ...page import models as page_models
from ...product import models as product_models
from ...shipping import models as shipping_models
from ..core.mutations import BaseMutation, ModelMutation, registry
# discount types need to be imported to get Voucher in the graphene registry
from ..discount import types  # noqa # pylint: disable=unused-import
from ..shop.types import Shop


class BaseTranslateMutation(ModelMutation):

    class Meta:
        abstract = True

    @classmethod
    @permission_required('site.manage_translations')
    def mutate(cls, root, info, **data):
        # DEMO: disable mutations
        raise PermissionDenied("Be aware admin pirate! API runs in read only mode!")

        errors = []
        model_type = registry.get_type_for_model(cls._meta.model)
        instance = cls.get_node_or_error(
            info, data['id'], errors, 'id', model_type)

        if errors:
            return cls(errors=errors)

        instance.translations.update_or_create(
            language_code=data['language_code'], defaults=data['input'])
        return cls(**{cls._meta.return_field_name: instance, 'errors': errors})


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
        id = graphene.ID(required=True, description='Category ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = TranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Category.'
        model = product_models.Category


class ProductTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description='Product ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = TranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Product.'
        model = product_models.Product


class CollectionTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description='Collection ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = TranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Collection.'
        model = product_models.Collection


class ProductVariantTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description='Product Variant ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = NameTranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Product Variant.'
        model = product_models.ProductVariant


class AttributeTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description='Attribute ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = NameTranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Attribute.'
        model = product_models.Attribute


class AttributeValueTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description='Attribute Value ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = NameTranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Attribute Value.'
        model = product_models.AttributeValue


class VoucherTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description='Voucher ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = NameTranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Voucher.'
        model = discount_models.Voucher


class ShippingPriceTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description='Shipping Method ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = NameTranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Shipping Method.'
        model = shipping_models.ShippingMethod


class MenuItemTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description='Menu Item ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = NameTranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Menu Item.'
        model = menu_models.MenuItem


class PageTranslationInput(SeoTranslationInput):
    title = graphene.String()
    content = graphene.String()
    content_json = graphene.JSONString()


class PageTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(required=True, description='Page ID')
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = PageTranslationInput(required=True)

    class Meta:
        description = 'Creates/Updates translations for Page.'
        model = page_models.Page


class ShopSettingsTranslationInput(graphene.InputObjectType):
    header_text = graphene.String()
    description = graphene.String()


class ShopSettingsTranslate(BaseMutation):
    shop = graphene.Field(Shop, description='Updated Shop')

    class Arguments:
        language_code = graphene.String(
            required=True, description='Translation language code')
        input = ShopSettingsTranslationInput(
            description=(
                'Fields required to update shop settings translations.'),
            required=True)

    class Meta:
        description = 'Creates/Updates translations for Shop Settings.'

    @classmethod
    @permission_required('site.manage_translations')
    def mutate(cls, root, info, language_code, input):
        # DEMO: disable mutations
        raise PermissionDenied("Be aware admin pirate! API runs in read only mode!")

        instance = info.context.site.settings
        instance.translations.update_or_create(
            language_code=language_code, defaults=input)
        return ShopSettingsTranslate(shop=Shop(), errors=[])
