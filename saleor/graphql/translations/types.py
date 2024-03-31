from typing import TypeVar

import graphene
from django.conf import settings
from django.db.models import Model

from ...attribute import AttributeInputType
from ...attribute import models as attribute_models
from ...attribute.models import AttributeValue
from ...discount import models as discount_models
from ...menu import models as menu_models
from ...page import models as page_models
from ...permission.enums import (
    DiscountPermissions,
    PagePermissions,
    ProductPermissions,
    ShippingPermissions,
)
from ...product import models as product_models
from ...shipping import models as shipping_models
from ...site import models as site_models
from ..attribute.dataloaders import AttributesByAttributeId, AttributeValueByIdLoader
from ..channel import ChannelContext
from ..core.context import get_database_connection_name
from ..core.descriptions import (
    ADDED_IN_39,
    ADDED_IN_314,
    ADDED_IN_317,
    DEPRECATED_IN_3X_FIELD,
    DEPRECATED_IN_3X_TYPE,
    RICH_CONTENT,
)
from ..core.enums import LanguageCodeEnum
from ..core.fields import JSONString, PermissionsField
from ..core.tracing import traced_resolver
from ..core.types import LanguageDisplay, ModelObjectType, NonNullList
from ..core.utils import str_to_enum
from ..discount.dataloaders import (
    PromotionByIdLoader,
    PromotionRuleByIdLoader,
    VoucherByIdLoader,
)
from ..menu.dataloaders import MenuItemByIdLoader
from ..page.dataloaders import (
    PageByIdLoader,
    SelectedAttributesAllByPageIdLoader,
    SelectedAttributesVisibleInStorefrontPageIdLoader,
)
from ..product.dataloaders import (
    CategoryByIdLoader,
    CollectionByIdLoader,
    ProductByIdLoader,
    ProductVariantByIdLoader,
    SelectedAttributesAllByProductIdLoader,
    SelectedAttributesByProductVariantIdLoader,
    SelectedAttributesVisibleInStorefrontByProductIdLoader,
)
from ..shipping.dataloaders import ShippingMethodByIdLoader
from ..utils import get_user_or_app_from_context
from .fields import TranslationField


def get_translatable_attribute_values(attributes: list) -> list[AttributeValue]:
    """Filter the list of passed attributes.

    Return those which are translatable attributes.
    """
    translatable_values: list[AttributeValue] = []
    for assignment in attributes:
        attr = assignment["attribute"]
        if attr.input_type in AttributeInputType.TRANSLATABLE_ATTRIBUTES:
            translatable_values.extend(assignment["values"])
    return translatable_values


T = TypeVar("T", bound=Model)


class BaseTranslationType(ModelObjectType[T]):
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


class AttributeValueTranslation(
    BaseTranslationType[attribute_models.AttributeValueTranslation]
):
    id = graphene.GlobalID(
        required=True, description="The ID of the attribute value translation."
    )
    name = graphene.String(
        required=True, description="Translated attribute value name."
    )
    rich_text = JSONString(
        description="Translated rich-text attribute value." + RICH_CONTENT
    )
    plain_text = graphene.String(description="Translated plain text attribute value .")
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.AttributeValueTranslatableContent",
        description="Represents the attribute value fields to translate."
        + ADDED_IN_314,
    )

    class Meta:
        model = attribute_models.AttributeValueTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents attribute value translations."

    @staticmethod
    def resolve_translatable_content(
        root: attribute_models.AttributeValueTranslation, info
    ):
        return AttributeValueByIdLoader(info.context).load(root.attribute_value_id)


class AttributeTranslation(BaseTranslationType[attribute_models.AttributeTranslation]):
    id = graphene.GlobalID(
        required=True, description="The ID of the attribute translation."
    )
    name = graphene.String(required=True, description="Translated attribute name.")
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.AttributeTranslatableContent",
        description="Represents the attribute fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = attribute_models.AttributeTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents attribute translations."

    @staticmethod
    def resolve_translatable_content(root: attribute_models.AttributeTranslation, info):
        return AttributesByAttributeId(info.context).load(root.attribute_id)


class AttributeTranslatableContent(ModelObjectType[attribute_models.Attribute]):
    id = graphene.GlobalID(
        required=True, description="The ID of the attribute translatable content."
    )
    attribute_id = graphene.ID(
        required=True,
        description="The ID of the attribute to translate." + ADDED_IN_314,
    )
    name = graphene.String(
        required=True, description="Name of the attribute to translate."
    )
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
        description = (
            "Represents attribute's original translatable fields "
            "and related translations."
        )

    @staticmethod
    def resolve_attribute(root: attribute_models.Attribute, _info):
        return root

    @staticmethod
    def resolve_attribute_id(root: attribute_models.Attribute, _info):
        return graphene.Node.to_global_id("Attribute", root.id)


class AttributeValueTranslatableContent(
    ModelObjectType[attribute_models.AttributeValue]
):
    id = graphene.GlobalID(
        required=True, description="The ID of the attribute value translatable content."
    )
    attribute_value_id = graphene.ID(
        required=True,
        description="The ID of the attribute value to translate." + ADDED_IN_314,
    )
    name = graphene.String(
        required=True,
        description="Name of the attribute value to translate.",
    )
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
    attribute = graphene.Field(
        AttributeTranslatableContent,
        description="Associated attribute that can be translated." + ADDED_IN_39,
    )

    class Meta:
        model = attribute_models.AttributeValue
        interfaces = [graphene.relay.Node]
        description = (
            "Represents attribute value's original translatable fields "
            "and related translations."
        )

    @staticmethod
    def resolve_attribute_value(root: attribute_models.AttributeValue, _info):
        return root

    @staticmethod
    def resolve_attribute(root: attribute_models.AttributeValue, info):
        return AttributesByAttributeId(info.context).load(root.attribute_id)

    @staticmethod
    def resolve_attribute_value_id(root: attribute_models.AttributeValue, _info):
        return graphene.Node.to_global_id("AttributeValue", root.id)


class ProductVariantTranslation(
    BaseTranslationType[product_models.ProductVariantTranslation]
):
    id = graphene.GlobalID(
        required=True, description="The ID of the product variant translation."
    )
    name = graphene.String(
        required=True, description="Translated product variant name."
    )
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.ProductVariantTranslatableContent",
        description="Represents the product variant fields to translate."
        + ADDED_IN_314,
    )

    class Meta:
        model = product_models.ProductVariantTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents product variant translations."

    @staticmethod
    def resolve_translatable_content(
        root: product_models.ProductVariantTranslation, info
    ):
        return ProductVariantByIdLoader(info.context).load(root.product_variant_id)


class ProductVariantTranslatableContent(ModelObjectType[product_models.ProductVariant]):
    id = graphene.GlobalID(
        required=True, description="The ID of the product variant translatable content."
    )
    product_variant_id = graphene.ID(
        required=True,
        description="The ID of the product variant to translate." + ADDED_IN_314,
    )
    name = graphene.String(
        required=True,
        description="Name of the product variant to translate.",
    )
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
        description = (
            "Represents product variant's original translatable fields "
            "and related translations."
        )

    @staticmethod
    def resolve_product_variant(root: product_models.ProductVariant, _info):
        return ChannelContext(node=root, channel_slug=None)

    @staticmethod
    def resolve_attribute_values(root: product_models.ProductVariant, info):
        return (
            SelectedAttributesByProductVariantIdLoader(info.context)
            .load(root.id)
            .then(get_translatable_attribute_values)
        )

    @staticmethod
    def resolve_product_variant_id(root: product_models.ProductVariant, _info):
        return graphene.Node.to_global_id("ProductVariant", root.id)


class ProductTranslation(BaseTranslationType[product_models.ProductTranslation]):
    id = graphene.GlobalID(
        required=True, description="The ID of the product translation."
    )
    seo_title = graphene.String(description="Translated SEO title.")
    seo_description = graphene.String(description="Translated SEO description.")
    name = graphene.String(description="Translated product name.")
    description = JSONString(
        description="Translated description of the product." + RICH_CONTENT
    )
    description_json = JSONString(
        description="Translated description of the product." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.ProductTranslatableContent",
        description="Represents the product fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = product_models.ProductTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents product translations."

    @staticmethod
    def resolve_description_json(root: product_models.ProductTranslation, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_translatable_content(root: product_models.ProductTranslation, info):
        return ProductByIdLoader(info.context).load(root.product_id)


class ProductTranslatableContent(ModelObjectType[product_models.Product]):
    id = graphene.GlobalID(
        required=True, description="The ID of the product translatable content."
    )
    product_id = graphene.ID(
        required=True,
        description="The ID of the product to translate." + ADDED_IN_314,
    )
    seo_title = graphene.String(description="SEO title to translate.")
    seo_description = graphene.String(description="SEO description to translate.")
    name = graphene.String(required=True, description="Product's name to translate.")
    description = JSONString(
        description="Product's description to translate." + RICH_CONTENT
    )
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
        description = (
            "Represents product's original translatable fields "
            "and related translations."
        )

    @staticmethod
    def resolve_product(root: product_models.Product, _info):
        return ChannelContext(node=root, channel_slug=None)

    @staticmethod
    def resolve_description_json(root: product_models.Product, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_attribute_values(root: product_models.Product, info):
        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(ProductPermissions.MANAGE_PRODUCTS)
        ):
            return (
                SelectedAttributesAllByProductIdLoader(info.context)
                .load(root.id)
                .then(get_translatable_attribute_values)
            )
        else:
            return (
                SelectedAttributesVisibleInStorefrontByProductIdLoader(info.context)
                .load(root.id)
                .then(get_translatable_attribute_values)
            )

    @staticmethod
    def resolve_product_id(root: product_models.Product, _info):
        return graphene.Node.to_global_id("Product", root.id)


class CollectionTranslation(BaseTranslationType[product_models.CollectionTranslation]):
    id = graphene.GlobalID(
        required=True, description="The ID of the collection translation."
    )
    seo_title = graphene.String(description="Translated SEO title.")
    seo_description = graphene.String(description="Translated SEO description.")
    name = graphene.String(description="Translated collection name.")
    description = JSONString(
        description="Translated description of the collection." + RICH_CONTENT
    )
    description_json = JSONString(
        description="Translated description of the collection." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.CollectionTranslatableContent",
        description="Represents the collection fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = product_models.CollectionTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents collection translations."

    @staticmethod
    def resolve_description_json(root: product_models.CollectionTranslation, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_translatable_content(root: product_models.CollectionTranslation, info):
        return CollectionByIdLoader(info.context).load(root.collection_id)


class CollectionTranslatableContent(ModelObjectType[product_models.Collection]):
    id = graphene.GlobalID(
        required=True, description="The ID of the collection translatable content."
    )
    collection_id = graphene.ID(
        required=True,
        description="The ID of the collection to translate." + ADDED_IN_314,
    )
    seo_title = graphene.String(description="SEO title to translate.")
    seo_description = graphene.String(description="SEO description to translate.")
    name = graphene.String(required=True, description="Collection's name to translate.")
    description = JSONString(
        description="Collection's description to translate." + RICH_CONTENT
    )
    description_json = JSONString(
        description="Description of the collection." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    translation = TranslationField(CollectionTranslation, type_name="collection")
    collection = graphene.Field(
        "saleor.graphql.product.types.collections.Collection",
        description="Represents a collection of products.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )

    class Meta:
        model = product_models.Collection
        interfaces = [graphene.relay.Node]
        description = (
            "Represents collection's original translatable fields "
            "and related translations."
        )

    @staticmethod
    def resolve_collection(root: product_models.Collection, info):
        collection = (
            product_models.Collection.objects.using(
                get_database_connection_name(info.context)
            )
            .all()
            .filter(pk=root.id)
            .first()
        )
        return (
            ChannelContext(node=collection, channel_slug=None) if collection else None
        )

    @staticmethod
    def resolve_description_json(root: product_models.Collection, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_collection_id(root: product_models.Collection, _info):
        return graphene.Node.to_global_id("Collection", root.id)


class CategoryTranslation(BaseTranslationType[product_models.CategoryTranslation]):
    id = graphene.GlobalID(
        required=True, description="The ID of the category translation."
    )
    seo_title = graphene.String(description="Translated SEO title.")
    seo_description = graphene.String(description="Translated SEO description.")
    name = graphene.String(description="Translated category name.")
    description = JSONString(
        description="Translated description of the category." + RICH_CONTENT
    )
    description_json = JSONString(
        description="Translated description of the category." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.CategoryTranslatableContent",
        description="Represents the category fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = product_models.CategoryTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents category translations."

    @staticmethod
    def resolve_description_json(root: product_models.CategoryTranslation, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_translatable_content(root: product_models.CategoryTranslation, info):
        return CategoryByIdLoader(info.context).load(root.category_id)


class CategoryTranslatableContent(ModelObjectType[product_models.Category]):
    id = graphene.GlobalID(
        required=True, description="The ID of the category translatable content."
    )
    category_id = graphene.ID(
        required=True,
        description="The ID of the category to translate." + ADDED_IN_314,
    )
    seo_title = graphene.String(description="SEO title to translate.")
    seo_description = graphene.String(description="SEO description to translate.")
    name = graphene.String(
        required=True, description="Name of the category translatable content."
    )
    description = JSONString(
        description="Category description to translate." + RICH_CONTENT
    )
    description_json = JSONString(
        description="Description of the category." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    translation = TranslationField(CategoryTranslation, type_name="category")
    category = graphene.Field(
        "saleor.graphql.product.types.categories.Category",
        description="Represents a single category of products.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Get model fields from the root level queries."
        ),
    )

    class Meta:
        model = product_models.Category
        interfaces = [graphene.relay.Node]
        description = (
            "Represents category original translatable fields and related translations."
        )

    @staticmethod
    def resolve_category(root: product_models.Category, _info):
        return root

    @staticmethod
    def resolve_description_json(root: product_models.Category, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_category_id(root: product_models.Category, _info):
        return graphene.Node.to_global_id("Category", root.id)


class PageTranslation(BaseTranslationType[page_models.PageTranslation]):
    id = graphene.GlobalID(required=True, description="The ID of the page translation.")
    seo_title = graphene.String(description="Translated SEO title.")
    seo_description = graphene.String(description="Translated SEO description.")
    title = graphene.String(description="Translated page title.")
    content = JSONString(description="Translated content of the page." + RICH_CONTENT)
    content_json = JSONString(
        description="Translated description of the page." + RICH_CONTENT,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use the `content` field instead.",
    )
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.PageTranslatableContent",
        description="Represents the page fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = page_models.PageTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents page translations."

    @staticmethod
    def resolve_content_json(root: page_models.PageTranslation, _info):
        content = root.content
        return content if content is not None else {}

    @staticmethod
    def resolve_translatable_content(root: page_models.PageTranslation, info):
        return PageByIdLoader(info.context).load(root.page_id)


class PageTranslatableContent(ModelObjectType[page_models.Page]):
    id = graphene.GlobalID(
        required=True, description="The ID of the page translatable content."
    )
    page_id = graphene.ID(
        required=True, description="The ID of the page to translate." + ADDED_IN_314
    )
    seo_title = graphene.String(description="SEO title to translate.")
    seo_description = graphene.String(description="SEO description to translate.")
    title = graphene.String(required=True, description="Page title to translate.")
    content = JSONString(description="Content of the page to translate." + RICH_CONTENT)
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
        description = (
            "Represents page's original translatable fields and related translations."
        )

    @staticmethod
    def resolve_page(root: page_models.Page, info):
        return (
            page_models.Page.objects.using(get_database_connection_name(info.context))
            .visible_to_user(info.context.user)
            .filter(pk=root.id)
            .first()
        )

    @staticmethod
    def resolve_content_json(root: page_models.Page, _info):
        content = root.content
        return content if content is not None else {}

    @staticmethod
    def resolve_attribute_values(root: page_models.Page, info):
        requestor = get_user_or_app_from_context(info.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(PagePermissions.MANAGE_PAGES)
        ):
            return (
                SelectedAttributesAllByPageIdLoader(info.context)
                .load(root.id)
                .then(get_translatable_attribute_values)
            )
        else:
            return (
                SelectedAttributesVisibleInStorefrontPageIdLoader(info.context)
                .load(root.id)
                .then(get_translatable_attribute_values)
            )

    @staticmethod
    def resolve_page_id(root: page_models.Page, _info):
        return graphene.Node.to_global_id("Page", root.id)


class VoucherTranslation(BaseTranslationType[discount_models.VoucherTranslation]):
    id = graphene.GlobalID(
        required=True, description="The ID of the voucher translation."
    )
    name = graphene.String(description="Translated voucher name.")
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.VoucherTranslatableContent",
        description="Represents the voucher fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = discount_models.VoucherTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents voucher translations."

    @staticmethod
    def resolve_translatable_content(root: discount_models.VoucherTranslation, info):
        return VoucherByIdLoader(info.context).load(root.voucher_id)


class VoucherTranslatableContent(ModelObjectType[discount_models.Voucher]):
    id = graphene.GlobalID(
        required=True, description="The ID of the voucher translatable content."
    )
    voucher_id = graphene.ID(
        required=True,
        description="The ID of the voucher to translate." + ADDED_IN_314,
    )
    name = graphene.String(description="Voucher name to translate.")
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
        description = (
            "Represents voucher's original translatable fields "
            "and related translations."
        )

    @staticmethod
    def resolve_voucher(root: discount_models.Voucher, _info):
        return ChannelContext(node=root, channel_slug=None)

    @staticmethod
    def resolve_voucher_id(root: discount_models.Voucher, _info):
        return graphene.Node.to_global_id("Voucher", root.id)


class SaleTranslation(BaseTranslationType[discount_models.PromotionTranslation]):
    id = graphene.GlobalID(required=True, description="The ID of the sale translation.")
    name = graphene.String(description="Translated name of sale.")
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.SaleTranslatableContent",
        description="Represents the sale fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = discount_models.PromotionTranslation
        interfaces = [graphene.relay.Node]
        description = (
            "Represents sale translations."
            + DEPRECATED_IN_3X_TYPE
            + " Use `PromotionTranslation` instead."
        )

    @staticmethod
    def resolve_translatable_content(root: discount_models.PromotionTranslation, info):
        return PromotionByIdLoader(info.context).load(root.promotion_id)


class SaleTranslatableContent(ModelObjectType[discount_models.Promotion]):
    id = graphene.GlobalID(
        required=True, description="The ID of the sale translatable content."
    )
    sale_id = graphene.ID(
        required=True,
        description="The ID of the sale to translate." + ADDED_IN_314,
    )
    name = graphene.String(required=True, description="Name of the sale to translate.")
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
        model = discount_models.Promotion
        interfaces = [graphene.relay.Node]
        description = (
            "Represents sale's original translatable fields and related translations."
            + DEPRECATED_IN_3X_TYPE
            + " Use `PromotionTranslatableContent` instead."
        )

    @staticmethod
    def resolve_sale(root: discount_models.Promotion, _info):
        return ChannelContext(node=root, channel_slug=None)

    @staticmethod
    def resolve_sale_id(root: discount_models.Promotion, _info):
        return graphene.Node.to_global_id("Sale", root.old_sale_id)


class ShopTranslation(BaseTranslationType[site_models.SiteSettingsTranslation]):
    id = graphene.GlobalID(required=True, description="The ID of the shop translation.")
    header_text = graphene.String(
        required=True, description="Translated header text of sale."
    )
    description = graphene.String(
        required=True, description="Translated description of sale."
    )

    class Meta:
        model = site_models.SiteSettingsTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents shop translations."


class MenuItemTranslation(BaseTranslationType[menu_models.MenuItemTranslation]):
    id = graphene.GlobalID(
        required=True, description="The ID of the menu item translation."
    )
    name = graphene.String(required=True, description="Translated menu item name.")
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.MenuItemTranslatableContent",
        description="Represents the menu item fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = menu_models.MenuItemTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents menu item translations."

    @staticmethod
    def resolve_translatable_content(root: menu_models.MenuItemTranslation, info):
        return MenuItemByIdLoader(info.context).load(root.menu_item_id)


class MenuItemTranslatableContent(ModelObjectType[menu_models.MenuItem]):
    id = graphene.GlobalID(
        required=True, description="The ID of the menu item translatable content."
    )
    menu_item_id = graphene.ID(
        required=True,
        description="The ID of the menu item to translate." + ADDED_IN_314,
    )
    name = graphene.String(
        required=True, description="Name of the menu item to translate."
    )
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
        description = (
            "Represents menu item's original translatable fields "
            "and related translations."
        )

    @staticmethod
    def resolve_menu_item(root: menu_models.MenuItem, _info):
        return ChannelContext(node=root, channel_slug=None)

    @staticmethod
    def resolve_menu_item_id(root: menu_models.MenuItem, _info):
        return graphene.Node.to_global_id("MenuItem", root.id)


class ShippingMethodTranslation(
    BaseTranslationType[shipping_models.ShippingMethodTranslation]
):
    id = graphene.GlobalID(
        required=True, description="The ID of the shipping method translation."
    )
    name = graphene.String(
        required=True, description="Translated shipping method name."
    )
    description = JSONString(
        description="Translated description of the shipping method." + RICH_CONTENT
    )
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.ShippingMethodTranslatableContent",
        description="Represents the shipping method fields to translate."
        + ADDED_IN_314,
    )

    class Meta:
        model = shipping_models.ShippingMethodTranslation
        interfaces = [graphene.relay.Node]
        description = "Represents shipping method translations."

    @staticmethod
    def resolve_translatable_content(
        root: shipping_models.ShippingMethodTranslation, info
    ):
        return ShippingMethodByIdLoader(info.context).load(root.shipping_method_id)


class ShippingMethodTranslatableContent(
    ModelObjectType[shipping_models.ShippingMethod]
):
    id = graphene.GlobalID(
        required=True, description="The ID of the shipping method translatable content."
    )
    shipping_method_id = graphene.ID(
        required=True,
        description="The ID of the shipping method to translate." + ADDED_IN_314,
    )
    name = graphene.String(
        required=True, description="Shipping method name to translate."
    )
    description = JSONString(
        description="Shipping method description to translate." + RICH_CONTENT
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
        description = (
            "Represents shipping method's original translatable fields "
            "and related translations."
        )

    @staticmethod
    def resolve_shipping_method(root: shipping_models.ShippingMethod, _info):
        return ChannelContext(node=root, channel_slug=None)

    @staticmethod
    def resolve_shipping_method_id(root: shipping_models.ShippingMethod, _info):
        return graphene.Node.to_global_id("ShippingMethodType", root.id)


class PromotionTranslation(BaseTranslationType[discount_models.PromotionTranslation]):
    id = graphene.GlobalID(
        required=True, description="ID of the promotion translation."
    )
    name = graphene.String(description="Translated name of the promotion.")
    description = JSONString(
        description="Translated description of the promotion." + RICH_CONTENT
    )
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.PromotionTranslatableContent",
        description="Represents the promotion fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = discount_models.Promotion
        interfaces = [graphene.relay.Node]
        description = "Represents promotion translations." + ADDED_IN_317

    @staticmethod
    def resolve_translatable_content(root: discount_models.PromotionTranslation, info):
        return PromotionByIdLoader(info.context).load(root.promotion_id)


class PromotionTranslatableContent(ModelObjectType[discount_models.Promotion]):
    id = graphene.GlobalID(
        required=True, description="ID of the promotion translatable content."
    )
    promotion_id = graphene.ID(
        required=True, description="ID of the promotion to translate."
    )
    name = graphene.String(required=True, description="Name of the promotion.")
    description = JSONString(description="Description of the promotion." + RICH_CONTENT)
    translation = TranslationField(PromotionTranslation, type_name="promotion")

    class Meta:
        model = discount_models.Promotion
        interfaces = [graphene.relay.Node]
        description = (
            "Represents promotion's original translatable fields "
            "and related translations." + ADDED_IN_317
        )

    @staticmethod
    def resolve_promotion_id(root: discount_models.Promotion, _info):
        return graphene.Node.to_global_id("Promotion", root.id)


class PromotionRuleTranslation(
    BaseTranslationType[discount_models.PromotionTranslation]
):
    id = graphene.GlobalID(
        required=True, description="ID of the promotion rule translation."
    )
    name = graphene.String(description="Translated name of the promotion rule.")
    description = JSONString(
        description="Translated description of the promotion rule." + RICH_CONTENT
    )
    translatable_content = graphene.Field(
        "saleor.graphql.translations.types.PromotionRuleTranslatableContent",
        description="Represents the promotion rule fields to translate." + ADDED_IN_314,
    )

    class Meta:
        model = discount_models.PromotionRule
        interfaces = [graphene.relay.Node]
        description = "Represents promotion rule translations." + ADDED_IN_317

    @staticmethod
    def resolve_translatable_content(
        root: discount_models.PromotionRuleTranslation, info
    ):
        return PromotionRuleByIdLoader(info.context).load(root.promotion_rule_id)


class PromotionRuleTranslatableContent(ModelObjectType[discount_models.Promotion]):
    id = graphene.GlobalID(
        required=True, description="ID of the promotion rule translatable content."
    )
    promotion_rule_id = graphene.ID(
        required=True,
        description="ID of the promotion rule to translate." + ADDED_IN_314,
    )
    name = graphene.String(description="Name of the promotion rule.")
    description = JSONString(
        description="Description of the promotion rule." + RICH_CONTENT
    )
    translation = TranslationField(PromotionRuleTranslation, type_name="promotion rule")

    class Meta:
        model = discount_models.PromotionRule
        interfaces = [graphene.relay.Node]
        description = (
            "Represents promotion rule's original translatable fields "
            "and related translations." + ADDED_IN_317
        )

    @staticmethod
    def resolve_promotion_rule_id(root: discount_models.PromotionRule, _info):
        return graphene.Node.to_global_id("PromotionRule", root.id)
