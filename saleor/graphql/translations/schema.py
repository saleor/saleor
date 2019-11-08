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


# TODO Consider name of this class, we should replace to TranslatableItem after
# `translations` query refactor. Issue #4957
class DefaultTranslationItem(graphene.Union):
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
    # TODO We nead to change output of this query to new types. Issue #4957
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
        # Disable all the no-member violations in this function
        # pylint: disable=no-member
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
