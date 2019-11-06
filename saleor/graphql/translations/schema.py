import graphene

from ...discount.models import Sale, Voucher
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
        )


class TranslatableItemConnection(CountableConnection):
    class Meta:
        node = TranslatableItem


class TranslatableKinds(graphene.Enum):
    ATTRIBUTE = "Attribute"
    ATTRIBUTE_VALUE = "Attribute value"
    CATEGORY = "Category"
    COLLECTION = "Collection"
    MENU_ITEM = "Menu item"
    PAGE = "Page"
    PRODUCT = "Product"
    SALE = "Sale"
    SHIPPING_METHOD = "Shipping method"
    VARIANT = "Variant"
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
    # TODO Add test for this query
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
        # TODO Add other translatable items
        if kind == TranslatableKinds.PRODUCT:  # TODO test hidden data
            _type, product_id = graphene.Node.from_global_id(id)
            return Product.objects.filter(pk=product_id).first()
        elif kind == TranslatableKinds.COLLECTION:  # TODO test hidden data
            _type, collection_id = graphene.Node.from_global_id(id)
            return Collection.objects.filter(pk=collection_id).first()
        elif kind == TranslatableKinds.CATEGORY:
            _type, category_id = graphene.Node.from_global_id(id)
            return Category.objects.filter(pk=category_id).first()
        elif kind == TranslatableKinds.ATTRIBUTE:
            _type, attribute_id = graphene.Node.from_global_id(id)
            return Attribute.objects.filter(pk=attribute_id).first()
        elif kind == TranslatableKinds.ATTRIBUTE_VALUE:
            _type, attribute_value_id = graphene.Node.from_global_id(id)
            return AttributeValue.objects.filter(pk=attribute_value_id).first()
        elif kind == TranslatableKinds.VARIANT:  # TODO test hidden data
            _type, product_variant_id = graphene.Node.from_global_id(id)
            return ProductVariant.objects.filter(pk=product_variant_id).first()
        elif kind == TranslatableKinds.PAGE:  # TODO test hidden data
            _type, page_id = graphene.Node.from_global_id(id)
            return Page.objects.filter(pk=page_id).first()
            # TODO test data not visible without perms
            # TODO No dashbord options to create translation create issue
        elif kind == TranslatableKinds.SHIPPING_METHOD:
            _type, shipping_method_id = graphene.Node.from_global_id(id)
            return ShippingMethod.objects.filter(pk=shipping_method_id).first()
        elif kind == TranslatableKinds.SALE:
            _type, sale_id = graphene.Node.from_global_id(id)
            return Sale.objects.filter(pk=sale_id).first()
        elif kind == TranslatableKinds.VOUCHER:
            _type, voucher_id = graphene.Node.from_global_id(id)
            return Voucher.objects.filter(pk=voucher_id).first()
