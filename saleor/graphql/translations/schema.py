import graphene

from ...attribute.models import Attribute, AttributeValue
from ...discount.models import Sale, Voucher
from ...menu.models import MenuItem
from ...page.models import Page
from ...permission.enums import SitePermissions
from ...product.models import Category, Collection, Product, ProductVariant
from ...shipping.models import ShippingMethod
from ..attribute.resolvers import resolve_attributes
from ..core import ResolveInfo
from ..core.connection import CountableConnection, create_connection_slice
from ..core.fields import ConnectionField, PermissionsField
from ..core.utils import from_global_id_or_error
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

TYPES_TRANSLATIONS_MAP = {
    Product: translation_types.ProductTranslatableContent,
    Collection: translation_types.CollectionTranslatableContent,
    Category: translation_types.CategoryTranslatableContent,
    Attribute: translation_types.AttributeTranslatableContent,
    AttributeValue: translation_types.AttributeValueTranslatableContent,
    ProductVariant: translation_types.ProductVariantTranslatableContent,
    Page: translation_types.PageTranslatableContent,
    ShippingMethod: translation_types.ShippingMethodTranslatableContent,
    Sale: translation_types.SaleTranslatableContent,
    Voucher: translation_types.VoucherTranslatableContent,
    MenuItem: translation_types.MenuItemTranslatableContent,
}


class TranslatableItem(graphene.Union):
    class Meta:
        types = tuple(TYPES_TRANSLATIONS_MAP.values())

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo):
        instance_type = type(instance)
        if instance_type in TYPES_TRANSLATIONS_MAP:
            return TYPES_TRANSLATIONS_MAP[instance_type]

        return super(TranslatableItem, cls).resolve_type(instance, info)


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
    SHIPPING_METHOD = "ShippingMethodType"
    VARIANT = "ProductVariant"
    VOUCHER = "Voucher"


class TranslationQueries(graphene.ObjectType):
    translations = ConnectionField(
        TranslatableItemConnection,
        description="Returns a list of all translatable items of a given kind.",
        kind=graphene.Argument(
            TranslatableKinds, required=True, description="Kind of objects to retrieve."
        ),
        permissions=[
            SitePermissions.MANAGE_TRANSLATIONS,
        ],
    )
    translation = PermissionsField(
        TranslatableItem,
        description="Lookup a translatable item by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the object to retrieve.", required=True
        ),
        kind=graphene.Argument(
            TranslatableKinds,
            required=True,
            description="Kind of the object to retrieve.",
        ),
        permissions=[SitePermissions.MANAGE_TRANSLATIONS],
    )

    @staticmethod
    def resolve_translations(_root, info: ResolveInfo, *, kind, **kwargs):
        if kind == TranslatableKinds.PRODUCT:
            qs = resolve_products(info)
        elif kind == TranslatableKinds.COLLECTION:
            qs = resolve_collections(info)
        elif kind == TranslatableKinds.CATEGORY:
            qs = resolve_categories(info)
        elif kind == TranslatableKinds.PAGE:
            qs = resolve_pages(info)
        elif kind == TranslatableKinds.SHIPPING_METHOD:
            qs = resolve_shipping_methods(info)
        elif kind == TranslatableKinds.VOUCHER:
            qs = resolve_vouchers(info)
        elif kind == TranslatableKinds.ATTRIBUTE:
            qs = resolve_attributes(info)
        elif kind == TranslatableKinds.ATTRIBUTE_VALUE:
            qs = resolve_attribute_values(info)
        elif kind == TranslatableKinds.VARIANT:
            qs = resolve_product_variants(info)
        elif kind == TranslatableKinds.MENU_ITEM:
            qs = resolve_menu_items(info)
        elif kind == TranslatableKinds.SALE:
            qs = resolve_sales(info)

        return create_connection_slice(qs, info, kwargs, TranslatableItemConnection)

    @staticmethod
    def resolve_translation(_root, _info: ResolveInfo, *, id, kind):
        _type, kind_id = from_global_id_or_error(id)
        if not _type == kind:
            return None
        models = {
            TranslatableKinds.PRODUCT.value: Product,  # type: ignore[attr-defined]
            TranslatableKinds.COLLECTION.value: Collection,  # type: ignore[attr-defined] # noqa: E501
            TranslatableKinds.CATEGORY.value: Category,  # type: ignore[attr-defined]
            TranslatableKinds.ATTRIBUTE.value: Attribute,  # type: ignore[attr-defined]
            TranslatableKinds.ATTRIBUTE_VALUE.value: AttributeValue,  # type: ignore[attr-defined] # noqa: E501
            TranslatableKinds.VARIANT.value: ProductVariant,  # type: ignore[attr-defined] # noqa: E501
            TranslatableKinds.PAGE.value: Page,  # type: ignore[attr-defined]
            TranslatableKinds.SHIPPING_METHOD.value: ShippingMethod,  # type: ignore[attr-defined] # noqa: E501
            TranslatableKinds.SALE.value: Sale,  # type: ignore[attr-defined]
            TranslatableKinds.VOUCHER.value: Voucher,  # type: ignore[attr-defined]
            TranslatableKinds.MENU_ITEM.value: MenuItem,  # type: ignore[attr-defined]
        }
        return models[kind].objects.filter(pk=kind_id).first()
