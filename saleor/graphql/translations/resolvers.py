from ...attribute import models as attribute_models
from ...discount import models as discount_models
from ...menu import models as menu_models
from ...page import models as page_models
from ...product import models as product_models
from ...shipping import interface as shipping_interface
from ...shipping import models as shipping_models
from ...site import models as site_models
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from . import dataloaders

TYPE_TO_TRANSLATION_LOADER_MAP = {
    attribute_models.Attribute: (
        dataloaders.AttributeTranslationByIdAndLanguageCodeLoader
    ),
    attribute_models.AttributeValue: (
        dataloaders.AttributeValueTranslationByIdAndLanguageCodeLoader
    ),
    product_models.Category: (dataloaders.CategoryTranslationByIdAndLanguageCodeLoader),
    product_models.Collection: (
        dataloaders.CollectionTranslationByIdAndLanguageCodeLoader
    ),
    menu_models.MenuItem: (dataloaders.MenuItemTranslationByIdAndLanguageCodeLoader),
    page_models.Page: dataloaders.PageTranslationByIdAndLanguageCodeLoader,
    product_models.Product: (dataloaders.ProductTranslationByIdAndLanguageCodeLoader),
    product_models.ProductVariant: (
        dataloaders.ProductVariantTranslationByIdAndLanguageCodeLoader
    ),
    shipping_models.ShippingMethod: (
        dataloaders.ShippingMethodTranslationByIdAndLanguageCodeLoader
    ),
    shipping_interface.ShippingMethodData: (
        dataloaders.ShippingMethodTranslationByIdAndLanguageCodeLoader
    ),
    site_models.SiteSettings: (
        dataloaders.SiteSettingsTranslationByIdAndLanguageCodeLoader
    ),
    discount_models.Voucher: (dataloaders.VoucherTranslationByIdAndLanguageCodeLoader),
    discount_models.Promotion: (
        dataloaders.PromotionTranslationByIdAndLanguageCodeLoader
    ),
    discount_models.PromotionRule: (
        dataloaders.PromotionRuleTranslationByIdAndLanguageCodeLoader
    ),
}


def resolve_translation(instance, info: ResolveInfo, *, language_code):
    """Get translation object from instance based on language code."""

    loader = TYPE_TO_TRANSLATION_LOADER_MAP.get(type(instance))
    if loader:
        return loader(info.context).load((instance.id, language_code))
    raise TypeError(f"No dataloader found to {type(instance)}")


def resolve_shipping_methods(info):
    return shipping_models.ShippingMethod.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_attribute_values(info):
    return attribute_models.AttributeValue.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_products(info):
    return product_models.Product.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_product_variants(info):
    return product_models.ProductVariant.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_sales(info):
    return discount_models.Promotion.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_vouchers(info):
    return discount_models.Voucher.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_collections(info):
    return product_models.Collection.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_promotions(info):
    return discount_models.Promotion.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_promotion_rules(info):
    return discount_models.PromotionRule.objects.using(
        get_database_connection_name(info.context)
    ).all()
