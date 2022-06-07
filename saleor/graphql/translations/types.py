from typing import List

import graphene
from django.conf import settings

from ...attribute import AttributeInputType
from ...attribute import models as attribute_models
from ...attribute.models import AttributeValue
from ...core.permissions import DiscountPermissions, ShippingPermissions
from ...core.tracing import traced_resolver
from ...discount import models as discount_models
from ...menu import models as menu_models
from ...page import models as page_models
from ...product import models as product_models
from ...shipping import models as shipping_models
from ...site import models as site_models
from ..channel import ChannelContext
from ..core.descriptions import DEPRECATED_IN_3X_FIELD, RICH_CONTENT
from ..core.enums import LanguageCodeEnum
from ..core.fields import JSONString, PermissionsField
from ..core.types import LanguageDisplay, ModelObjectType, NonNullList
from ..core.utils import str_to_enum
from ..page.dataloaders import SelectedAttributesByPageIdLoader
from ..product.dataloaders import (
    SelectedAttributesByProductIdLoader,
    SelectedAttributesByProductVariantIdLoader,
)
from .fields import TranslationField


def get_translatable_attribute_values(attributes: list) -> List[AttributeValue]:
    """Filter the list of passed attributes.

    Return those which are translatable attributes.
    """
    translatable_values: List[AttributeValue] = []
    for assignment in attributes:
        attr = assignment["attribute"]
        if attr.input_type in AttributeInputType.TRANSLATABLE_ATTRIBUTES:
            translatable_values.extend(assignment["values"])
    return translatable_values


class BaseTranslationType(ModelObjectType):
    language = graphene.Field(
        LanguageDisplay, description="Translation language.", required=True
    )

    class Meta:
        abstract = True

    @staticmethod
    @traced_resolver
    def resolve_language(root, _info):
        try:
            language = next(
                language[1]
                for language in settings.LANGUAGES
                if language[0] == root.language_code
            )
        except StopIteration:
            return None
        return LanguageDisplay(
            code=LanguageCodeEnum[str_to_enum(root.language_code)], language=language
        )


class AttributeValueTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    rich_text = JSONString(description="Attribute value." + RICH_CONTENT)
    plain_text = graphene.String(description="Attribute plain text value.")

    class Meta:
        model = attribute_models.AttributeValueTranslation
        interfaces = [graphene.relay.Node]


class AttributeValueTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    rich_text = JSONString(description="Attribute value." + RICH_CONTENT)
    plain_text = graphene.String(description="Attribute plain text value.")
    translation = TranslationField(
        AttributeValueTranslation, type_name="attribute value"
    )
    attribute_value = graphene.Field(
        "saleor.graphql.attribute.types.AttributeValue",
        description="Represents a value of an attribute.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )

    class Meta:
        model = attribute_models.AttributeValue
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_attribute_value(root: attribute_models.AttributeValue, _info):
        return root


class AttributeTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)

    class Meta:
        model = attribute_models.AttributeTranslation
        interfaces = [graphene.relay.Node]


class AttributeTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    translation = TranslationField(AttributeTranslation, type_name="attribute")
    attribute = graphene.Field(
        "saleor.graphql.attribute.types.Attribute",
        description="Custom attribute of a product.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )

    class Meta:
        model = attribute_models.Attribute
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_attribute(root: attribute_models.Attribute, _info):
        return root


class ProductVariantTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)

    class Meta:
        model = product_models.ProductVariantTranslation
        interfaces = [graphene.relay.Node]


class ProductVariantTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    translation = TranslationField(
        ProductVariantTranslation, type_name="product variant"
    )
    product_variant = graphene.Field(
        "saleor.graphql.product.types.products.ProductVariant",
        description=(
            "Represents a version of a product such as different size or color."
        ),
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )
    attribute_values = NonNullList(
        AttributeValueTranslatableContent,
        required=True,
        description="List of product variant attribute values that can be translated.",
    )

    class Meta:
        model = product_models.ProductVariant
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_product_variant(root: product_models.ProductVariant, info):
        return ChannelContext(node=root, channel_slug=None)

    @staticmethod
    def resolve_attribute_values(root: product_models.ProductVariant, info):
        return (
            SelectedAttributesByProductVariantIdLoader(info.context)
            .load(root.id)
            .then(get_translatable_attribute_values)
        )


class ProductTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String()
    description = JSONString(
        description="Translated description of the product." + RICH_CONTENT
    )
    description_json = JSONString(
        description="Translated description of the product." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )

    class Meta:
        model = product_models.ProductTranslation
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_description_json(root: product_models.ProductTranslation, _info):
        description = root.description
        return description if description is not None else {}


class ProductTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String(required=True)
    description = JSONString(description="Description of the product." + RICH_CONTENT)
    description_json = JSONString(
        description="Description of the product." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    translation = TranslationField(ProductTranslation, type_name="product")
    product = graphene.Field(
        "saleor.graphql.product.types.products.Product",
        description="Represents an individual item for sale in the storefront.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )
    attribute_values = NonNullList(
        AttributeValueTranslatableContent,
        required=True,
        description="List of product attribute values that can be translated.",
    )

    class Meta:
        model = product_models.Product
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_product(root: product_models.Product, info):
        return ChannelContext(node=root, channel_slug=None)

    @staticmethod
    def resolve_description_json(root: product_models.Product, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_attribute_values(root: product_models.Product, info):
        return (
            SelectedAttributesByProductIdLoader(info.context)
            .load(root.id)
            .then(get_translatable_attribute_values)
        )


class CollectionTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String()
    description = JSONString(
        description="Translated description of the collection." + RICH_CONTENT
    )
    description_json = JSONString(
        description="Translated description of the collection." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )

    class Meta:
        model = product_models.CollectionTranslation
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_description_json(root: product_models.CollectionTranslation, _info):
        description = root.description
        return description if description is not None else {}


class CollectionTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String(required=True)
    description = JSONString(
        description="Description of the collection." + RICH_CONTENT
    )
    description_json = JSONString(
        description="Description of the collection." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    translation = TranslationField(CollectionTranslation, type_name="collection")
    collection = graphene.Field(
        "saleor.graphql.product.types.products.Collection",
        description="Represents a collection of products.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )

    class Meta:
        model = product_models.Collection
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_collection(root: product_models.Collection, info):
        collection = product_models.Collection.objects.all().filter(pk=root.id).first()
        return (
            ChannelContext(node=collection, channel_slug=None) if collection else None
        )

    @staticmethod
    def resolve_description_json(root: product_models.Collection, _info):
        description = root.description
        return description if description is not None else {}


class CategoryTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String()
    description = JSONString(
        description="Translated description of the category." + RICH_CONTENT
    )
    description_json = JSONString(
        description="Translated description of the category." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )

    class Meta:
        model = product_models.CategoryTranslation
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_description_json(root: product_models.CategoryTranslation, _info):
        description = root.description
        return description if description is not None else {}


class CategoryTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String(required=True)
    description = JSONString(description="Description of the category." + RICH_CONTENT)
    description_json = JSONString(
        description="Description of the category." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    translation = TranslationField(CategoryTranslation, type_name="category")
    category = graphene.Field(
        "saleor.graphql.product.types.products.Category",
        description="Represents a single category of products.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )

    class Meta:
        model = product_models.Category
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_category(root: product_models.Category, _info):
        return root

    @staticmethod
    def resolve_description_json(root: product_models.Category, _info):
        description = root.description
        return description if description is not None else {}


class PageTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    title = graphene.String()
    content = JSONString(description="Translated content of the page." + RICH_CONTENT)
    content_json = JSONString(
        description="Translated description of the page." + RICH_CONTENT,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use the `content` field instead.",
    )

    class Meta:
        model = page_models.PageTranslation
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_content_json(root: page_models.PageTranslation, _info):
        content = root.content
        return content if content is not None else {}


class PageTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    title = graphene.String(required=True)
    content = JSONString(description="Content of the page." + RICH_CONTENT)
    content_json = JSONString(
        description="Content of the page." + RICH_CONTENT,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use the `content` field instead.",
    )
    translation = TranslationField(PageTranslation, type_name="page")
    page = graphene.Field(
        "saleor.graphql.page.types.Page",
        description=(
            "A static page that can be manually added by a shop operator "
            "through the dashboard."
        ),
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )
    attribute_values = NonNullList(
        AttributeValueTranslatableContent,
        required=True,
        description="List of page content attribute values that can be translated.",
    )

    class Meta:
        model = page_models.Page
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_page(root: page_models.Page, info):
        return (
            page_models.Page.objects.visible_to_user(info.context.user)
            .filter(pk=root.id)
            .first()
        )

    @staticmethod
    def resolve_content_json(root: page_models.Page, _info):
        content = root.content
        return content if content is not None else {}

    @staticmethod
    def resolve_attribute_values(root: page_models.Page, info):
        return (
            SelectedAttributesByPageIdLoader(info.context)
            .load(root.id)
            .then(get_translatable_attribute_values)
        )


class VoucherTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    name = graphene.String()

    class Meta:
        model = discount_models.VoucherTranslation
        interfaces = [graphene.relay.Node]


class VoucherTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String()
    translation = TranslationField(VoucherTranslation, type_name="voucher")
    voucher = PermissionsField(
        "saleor.graphql.discount.types.Voucher",
        description=(
            "Vouchers allow giving discounts to particular customers on categories, "
            "collections or specific products. They can be used during checkout by "
            "providing valid voucher codes."
        ),
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
        permissions=[DiscountPermissions.MANAGE_DISCOUNTS],
    )

    class Meta:
        model = discount_models.Voucher
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_voucher(root: discount_models.Voucher, _info):
        return ChannelContext(node=root, channel_slug=None)


class SaleTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    name = graphene.String()

    class Meta:
        model = discount_models.SaleTranslation
        interfaces = [graphene.relay.Node]


class SaleTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    translation = TranslationField(SaleTranslation, type_name="sale")
    sale = PermissionsField(
        "saleor.graphql.discount.types.Sale",
        description=(
            "Sales allow creating discounts for categories, collections "
            "or products and are visible to all the customers."
        ),
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
        permissions=[DiscountPermissions.MANAGE_DISCOUNTS],
    )

    class Meta:
        model = discount_models.Sale
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_sale(root: discount_models.Sale, _info):
        return ChannelContext(node=root, channel_slug=None)


class ShopTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    header_text = graphene.String(required=True)
    description = graphene.String(required=True)

    class Meta:
        model = site_models.SiteSettingsTranslation
        interfaces = [graphene.relay.Node]


class MenuItemTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)

    class Meta:
        model = menu_models.MenuItemTranslation
        interfaces = [graphene.relay.Node]


class MenuItemTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    translation = TranslationField(MenuItemTranslation, type_name="menu item")
    menu_item = graphene.Field(
        "saleor.graphql.menu.types.MenuItem",
        description=(
            "Represents a single item of the related menu. Can store categories, "
            "collection or pages."
        ),
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )

    class Meta:
        model = menu_models.MenuItem
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_menu_item(root: menu_models.MenuItem, _info):
        return ChannelContext(node=root, channel_slug=None)


class ShippingMethodTranslation(BaseTranslationType):
    id = graphene.GlobalID(required=True)
    name = graphene.String()
    description = JSONString(
        description="Translated description of the shipping method." + RICH_CONTENT
    )

    class Meta:
        model = shipping_models.ShippingMethodTranslation
        interfaces = [graphene.relay.Node]


class ShippingMethodTranslatableContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    description = JSONString(
        description="Description of the shipping method." + RICH_CONTENT
    )
    translation = TranslationField(
        ShippingMethodTranslation, type_name="shipping method"
    )
    shipping_method = PermissionsField(
        "saleor.graphql.shipping.types.ShippingMethodType",
        description=(
            "Shipping method are the methods you'll use to get customer's orders "
            " to them. They are directly exposed to the customers."
        ),
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
        permissions=[
            ShippingPermissions.MANAGE_SHIPPING,
        ],
    )

    class Meta:
        model = shipping_models.ShippingMethod
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_shipping_method(root: shipping_models.ShippingMethod, _info):
        return ChannelContext(node=root, channel_slug=None)
