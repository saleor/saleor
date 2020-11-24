import graphene

from ...attribute.models import Attribute, AttributeValue
from ...core.permissions import SitePermissions
from ...discount.models import Sale, Voucher
from ...menu.models import MenuItem
from ...page.models import Page
from ...product.models import Category, Collection, Product, ProductVariant
from ...shipping.models import ShippingMethod
from ..attribute.resolvers import resolve_attributes
from ..core.connection import CountableConnection
from ..core.fields import BaseConnectionField
from ..decorators import permission_required
from ..menu.resolvers import resolve_menu_items
from ..page.resolvers import resolve_pages
from ..product.resolvers import resolve_categories
from ..translations import types as translation_types
from .resolvers import (
    resolve_attribute_values,
    resolve_collections,
    resolve_product_variants,
    resolve_products,
    resolve_sales,
    resolve_shipping_methods,
    resolve_vouchers,
)


class TranslatableItem(graphene.Union):
    class Meta:
        types = (
            translation_types.ProductTranslatableContent,
            translation_types.CollectionTranslatableContent,
            translation_types.CategoryTranslatableContent,
            translation_types.AttributeTranslatableContent,
            translation_types.AttributeValueTranslatableContent,
            translation_types.ProductVariantTranslatableContent,
            translation_types.PageTranslatableContent,
            translation_types.ShippingMethodTranslatableContent,
            translation_types.SaleTranslatableContent,
            translation_types.VoucherTranslatableContent,
            translation_types.MenuItemTranslatableContent,
        )


class TranslatableItemConnection(CountableConnection):
    class Meta:
        node = TranslatableItem


class TranslatableKinds(graphene.Enum):
    ATTRIBUTE = "Attribute"
    ATTRIBUTE_VALUE = "AttributeValue"
    CATEGORY = "Category"
    COLLECTION = "Collection"
    MENU_ITEM = "MenuItem"
    PAGE = "Page"
    PRODUCT = "Product"
    SALE = "Sale"
    SHIPPING_METHOD = "ShippingMethod"
    VARIANT = "ProductVariant"
    VOUCHER = "Voucher"


class TranslationQueries(graphene.ObjectType):
    translations = BaseConnectionField(
        TranslatableItemConnection,
        description="Returns a list of all translatable items of a given kind.",
        kind=graphene.Argument(
            TranslatableKinds, required=True, description="Kind of objects to retrieve."
        ),
    )
    translation = graphene.Field(
        TranslatableItem,
        id=graphene.Argument(
            graphene.ID, description="ID of the object to retrieve.", required=True
        ),
        kind=graphene.Argument(
            TranslatableKinds,
            required=True,
            description="Kind of the object to retrieve.",
        ),
    )

    @permission_required(SitePermissions.MANAGE_TRANSLATIONS)
    def resolve_translations(self, info, kind, **_kwargs):
        if kind == TranslatableKinds.PRODUCT:
            return resolve_products(info)
        elif kind == TranslatableKinds.COLLECTION:
            return resolve_collections(info)
        elif kind == TranslatableKinds.CATEGORY:
            return resolve_categories(info, query=None)
        elif kind == TranslatableKinds.PAGE:
            return resolve_pages(info, query=None)
        elif kind == TranslatableKinds.SHIPPING_METHOD:
            return resolve_shipping_methods(info)
        elif kind == TranslatableKinds.VOUCHER:
            return resolve_vouchers(info)
        elif kind == TranslatableKinds.ATTRIBUTE:
            return resolve_attributes(info)
        elif kind == TranslatableKinds.ATTRIBUTE_VALUE:
            return resolve_attribute_values(info)
        elif kind == TranslatableKinds.VARIANT:
            return resolve_product_variants(info)
        elif kind == TranslatableKinds.MENU_ITEM:
            return resolve_menu_items(info, query=None)
        elif kind == TranslatableKinds.SALE:
            return resolve_sales(info)

    @permission_required(SitePermissions.MANAGE_TRANSLATIONS)
    def resolve_translation(self, info, id, kind, **_kwargs):
        _type, kind_id = graphene.Node.from_global_id(id)
        if not _type == kind:
            return None
        models = {
            TranslatableKinds.PRODUCT.value: Product,
            TranslatableKinds.COLLECTION.value: Collection,
            TranslatableKinds.CATEGORY.value: Category,
            TranslatableKinds.ATTRIBUTE.value: Attribute,
            TranslatableKinds.ATTRIBUTE_VALUE.value: AttributeValue,
            TranslatableKinds.VARIANT.value: ProductVariant,
            TranslatableKinds.PAGE.value: Page,
            TranslatableKinds.SHIPPING_METHOD.value: ShippingMethod,
            TranslatableKinds.SALE.value: Sale,
            TranslatableKinds.VOUCHER.value: Voucher,
            TranslatableKinds.MENU_ITEM.value: MenuItem,
        }
        return models[kind].objects.filter(pk=kind_id).first()
