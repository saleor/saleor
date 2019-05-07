import graphene

from ..core.connection import CountableConnection
from ..discount import types as discount_types
from ..discount.resolvers import resolve_sales, resolve_vouchers
from ..menu import types as menu_types
from ..menu.resolvers import resolve_menu_items
from ..page import types as page_types
from ..page.resolvers import resolve_pages
from ..product import types as product_types
from ..product.resolvers import (
    resolve_attributes, resolve_categories, resolve_collections,
    resolve_product_variants, resolve_products)
from ..shipping import types as shipping_types
from .resolvers import resolve_attribute_values, resolve_shipping_methods


class TranslatableItem(graphene.Union):
    class Meta:
        types = (
            product_types.Product,
            product_types.Category,
            product_types.Collection,
            product_types.Attribute,
            product_types.AttributeValue,
            product_types.ProductVariant,
            page_types.Page,
            shipping_types.ShippingMethod,
            discount_types.Sale,
            discount_types.Voucher,
            menu_types.MenuItem)


class TranslatableItemConnection(CountableConnection):
    class Meta:
        node = TranslatableItem


class TranslatableKinds(graphene.Enum):
    ATTRIBUTE = 'Attribute'
    ATTRIBUTE_VALUE = 'Attribute Value'
    CATEGORY = 'Category'
    COLLECTION = 'Collection'
    MENU_ITEM = 'Menu Item'
    PAGE = 'Page'
    PRODUCT = 'Product'
    SALE = 'Sale'
    SHIPPING_METHOD = 'Shipping Method'
    VARIANT = 'Variant'
    VOUCHER = 'Voucher'


class TranslationQueries(graphene.ObjectType):
    translations = graphene.ConnectionField(
        TranslatableItemConnection,
        description='Returns list of all translatable items of a given kind.',
        kind=graphene.Argument(
            TranslatableKinds,
            required=True, description='Kind of objects to retrieve.'))

    def resolve_translations(self, info, kind, **_kwargs):
        if kind == TranslatableKinds.PRODUCT:
            return resolve_products(info)
        elif kind == TranslatableKinds.COLLECTION:
            return resolve_collections(info, query=None)
        elif kind == TranslatableKinds.CATEGORY:
            return resolve_categories(info, query=None)
        elif kind == TranslatableKinds.PAGE:
            return resolve_pages(info, query=None)
        elif kind == TranslatableKinds.SHIPPING_METHOD:
            return resolve_shipping_methods(info)
        elif kind == TranslatableKinds.VOUCHER:
            return resolve_vouchers(info, query=None)
        elif kind == TranslatableKinds.ATTRIBUTE:
            return resolve_attributes(info)
        elif kind == TranslatableKinds.ATTRIBUTE_VALUE:
            return resolve_attribute_values(info)
        elif kind == TranslatableKinds.VARIANT:
            return resolve_product_variants(info)
        elif kind == TranslatableKinds.MENU_ITEM:
            return resolve_menu_items(info, query=None)
        elif kind == TranslatableKinds.SALE:
            return resolve_sales(info, query=None)
