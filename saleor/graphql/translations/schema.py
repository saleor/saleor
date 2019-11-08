import graphene

from ...discount.models import Sale, Voucher
from ...menu.models import MenuItem
from ...page.models import Page
from ...product.models import (
    Attribute,
    AttributeValue,
    Category,
    Collection,
    Product,
    ProductVariant,
)
from ...shipping.models import ShippingMethod
from ..core.connection import CountableConnection
from ..core.fields import BaseConnectionField
from ..decorators import permission_required
from ..discount import types as discount_types
from ..discount.resolvers import resolve_sales, resolve_vouchers
from ..menu import types as menu_types
from ..menu.resolvers import resolve_menu_items
from ..page import types as page_types
from ..page.resolvers import resolve_pages
from ..product import types as product_types
from ..product.resolvers import (
    resolve_attributes,
    resolve_categories,
    resolve_collections,
    resolve_product_variants,
    resolve_products,
)
from ..shipping import types as shipping_types
from ..translations import types as translation_types
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
            menu_types.MenuItem,
        )


# TODO Consider name of this class, maby we should replace TranslatableItem
class DefaultTranslationItem(graphene.Union):
    class Meta:
        types = (
            translation_types.ProductStrings,
            translation_types.CollectionStrings,
            translation_types.CategoryStrings,
            translation_types.AttributeStrings,
            translation_types.AttributeValueStrings,
            translation_types.ProductVariantStrings,
            translation_types.PageStrings,
            translation_types.ShippingMethodStrings,
            translation_types.SaleStrings,
            translation_types.VoucherStrings,
            translation_types.MenuItemStrings,
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
    # TODO We nead to change output of this query to new types
    translations = BaseConnectionField(
        TranslatableItemConnection,
        description="Returns a list of all translatable items of a given kind.",
        kind=graphene.Argument(
            TranslatableKinds, required=True, description="Kind of objects to retrieve."
        ),
    )
    translation = graphene.Field(
        DefaultTranslationItem,
        id=graphene.Argument(
            graphene.ID, description="ID of the objects to retrieve.", required=True
        ),
        kind=graphene.Argument(
            TranslatableKinds, required=True, description="Kind of objects to retrieve."
        ),
    )

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

    @permission_required("site.manage_translations")
    def resolve_translation(self, info, id, kind, **_kwargs):
        _type, kind_id = graphene.Node.from_global_id(id)
        if not _type == kind:
            return None
        if kind == TranslatableKinds.PRODUCT:
            return Product.objects.filter(pk=kind_id).first()
        elif kind == TranslatableKinds.COLLECTION:
            return Collection.objects.filter(pk=kind_id).first()
        elif kind == TranslatableKinds.CATEGORY:
            return Category.objects.filter(pk=kind_id).first()
        elif kind == TranslatableKinds.ATTRIBUTE:
            return Attribute.objects.filter(pk=kind_id).first()
        elif kind == TranslatableKinds.ATTRIBUTE_VALUE:
            return AttributeValue.objects.filter(pk=kind_id).first()
        elif kind == TranslatableKinds.VARIANT:
            return ProductVariant.objects.filter(pk=kind_id).first()
        elif kind == TranslatableKinds.PAGE:
            return Page.objects.filter(pk=kind_id).first()
            # TODO No dashbord options to create translation create issue
        elif kind == TranslatableKinds.SHIPPING_METHOD:
            return ShippingMethod.objects.filter(pk=kind_id).first()
        elif kind == TranslatableKinds.SALE:
            return Sale.objects.filter(pk=kind_id).first()
        elif kind == TranslatableKinds.VOUCHER:
            return Voucher.objects.filter(pk=kind_id).first()
            # TODO No dashbord options to create translation create issue
        elif kind == TranslatableKinds.MENU_ITEM:
            return MenuItem.objects.filter(pk=kind_id).first()
