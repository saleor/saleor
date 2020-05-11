from dataclasses import asdict
from typing import List, Union

import graphene
from graphene import relay
from graphene_federation import key
from graphql.error import GraphQLError

from ....core.permissions import ProductPermissions
from ....product import models
from ....product.templatetags.product_images import (
    get_product_image_thumbnail,
    get_thumbnail,
)
from ....product.utils import calculate_revenue_for_variant
from ....product.utils.availability import (
    get_product_availability,
    get_variant_availability,
)
from ....product.utils.costs import get_margin_for_variant, get_product_costs_data
from ....warehouse.availability import (
    get_available_quantity,
    get_available_quantity_for_customer,
    get_quantity_allocated,
    is_product_in_stock,
    is_variant_in_stock,
)
from ...account.enums import CountryCodeEnum
from ...core.connection import CountableDjangoObjectType
from ...core.enums import ReportingPeriod, TaxRateType
from ...core.fields import FilterInputConnectionField, PrefetchingConnectionField
from ...core.types import Image, Money, MoneyRange, TaxedMoney, TaxedMoneyRange, TaxType
from ...decorators import permission_required
from ...discount.dataloaders import DiscountsByDateTimeLoader
from ...meta.deprecated.resolvers import resolve_meta, resolve_private_meta
from ...meta.types import ObjectWithMetadata
from ...translations.fields import TranslationField
from ...translations.types import (
    CategoryTranslation,
    CollectionTranslation,
    ProductTranslation,
    ProductVariantTranslation,
)
from ...utils import get_database_id
from ...utils.filters import reporting_period_to_date
from ...warehouse.types import Stock
from ..dataloaders import (
    CategoryByIdLoader,
    CollectionsByProductIdLoader,
    ImagesByProductIdLoader,
    ProductByIdLoader,
    ProductVariantsByProductIdLoader,
    SelectedAttributesByProductIdLoader,
    SelectedAttributesByProductVariantIdLoader,
)
from ..filters import AttributeFilterInput
from ..resolvers import resolve_attributes
from .attributes import Attribute, SelectedAttribute
from .digital_contents import DigitalContent


def resolve_attribute_list(
    instance: Union[models.Product, models.ProductVariant], *, user
) -> List[SelectedAttribute]:
    """Resolve attributes from a product into a list of `SelectedAttribute`s.

    Note: you have to prefetch the below M2M fields.
        - product_type -> attribute[rel] -> [rel]assignments -> values
        - product_type -> attribute[rel] -> attribute
    """
    resolved_attributes = []
    attributes_qs = None

    # Retrieve the product type
    if isinstance(instance, models.Product):
        product_type = instance.product_type
        product_type_attributes_assoc_field = "attributeproduct"
        assigned_attribute_instance_field = "productassignments"
        assigned_attribute_instance_filters = {"product_id": instance.pk}
        if hasattr(product_type, "storefront_attributes"):
            attributes_qs = product_type.storefront_attributes  # type: ignore
    elif isinstance(instance, models.ProductVariant):
        product_type = instance.product.product_type
        product_type_attributes_assoc_field = "attributevariant"
        assigned_attribute_instance_field = "variantassignments"
        assigned_attribute_instance_filters = {"variant_id": instance.pk}
    else:
        raise AssertionError(f"{instance.__class__.__name__} is unsupported")

    # Retrieve all the product attributes assigned to this product type
    if not attributes_qs:
        attributes_qs = getattr(product_type, product_type_attributes_assoc_field)
        attributes_qs = attributes_qs.get_visible_to_user(user)

    # An empty QuerySet for unresolved values
    empty_qs = models.AttributeValue.objects.none()

    # Goes through all the attributes assigned to the product type
    # The assigned values are returned as a QuerySet, but will assign a
    # dummy empty QuerySet if no values are assigned to the given instance.
    for attr_data_rel in attributes_qs:
        attr_instance_data = getattr(attr_data_rel, assigned_attribute_instance_field)

        # Retrieve the instance's associated data
        attr_data = attr_instance_data.filter(**assigned_attribute_instance_filters)
        attr_data = attr_data.first()

        # Return the instance's attribute values if the assignment was found,
        # otherwise it sets the values as an empty QuerySet
        values = attr_data.values.all() if attr_data is not None else empty_qs
        resolved_attributes.append(
            SelectedAttribute(attribute=attr_data_rel.attribute, values=values)
        )
    return resolved_attributes


class Margin(graphene.ObjectType):
    start = graphene.Int()
    stop = graphene.Int()


class BasePricingInfo(graphene.ObjectType):
    on_sale = graphene.Boolean(description="Whether it is in sale or not.")
    discount = graphene.Field(
        TaxedMoney, description="The discount amount if in sale (null otherwise)."
    )
    discount_local_currency = graphene.Field(
        TaxedMoney, description="The discount amount in the local currency."
    )


class VariantPricingInfo(BasePricingInfo):
    discount_local_currency = graphene.Field(
        TaxedMoney, description="The discount amount in the local currency."
    )
    price = graphene.Field(
        TaxedMoney, description="The price, with any discount subtracted."
    )
    price_undiscounted = graphene.Field(
        TaxedMoney, description="The price without any discount."
    )
    price_local_currency = graphene.Field(
        TaxedMoney, description="The discounted price in the local currency."
    )

    class Meta:
        description = "Represents availability of a variant in the storefront."


class ProductPricingInfo(BasePricingInfo):
    price_range = graphene.Field(
        TaxedMoneyRange,
        description="The discounted price range of the product variants.",
    )
    price_range_undiscounted = graphene.Field(
        TaxedMoneyRange,
        description="The undiscounted price range of the product variants.",
    )
    price_range_local_currency = graphene.Field(
        TaxedMoneyRange,
        description=(
            "The discounted price range of the product variants "
            "in the local currency."
        ),
    )

    class Meta:
        description = "Represents availability of a product in the storefront."


@key(fields="id")
class ProductVariant(CountableDjangoObjectType):
    quantity = graphene.Int(
        required=True,
        description="Quantity of a product available for sale.",
        deprecation_reason=(
            "Use the stock field instead. This field will be removed after 2020-07-31."
        ),
    )
    quantity_allocated = graphene.Int(
        required=False,
        description="Quantity allocated for orders.",
        deprecation_reason=(
            "Use the stock field instead. This field will be removed after 2020-07-31."
        ),
    )
    stock_quantity = graphene.Int(
        required=True,
        description="Quantity of a product available for sale.",
        deprecation_reason=(
            "Use the stock field instead. This field will be removed after 2020-07-31."
        ),
    )
    price_override = graphene.Field(
        Money,
        description=(
            "Override the base price of a product if necessary. A value of `null` "
            "indicates that the default product price is used."
        ),
    )
    pricing = graphene.Field(
        VariantPricingInfo,
        description=(
            "Lists the storefront variant's pricing, the current price and discounts, "
            "only meant for displaying."
        ),
    )
    is_available = graphene.Boolean(
        description="Whether the variant is in stock and visible or not.",
        deprecation_reason=(
            "Use the stock field instead. This field will be removed after 2020-07-31."
        ),
    )

    attributes = graphene.List(
        graphene.NonNull(SelectedAttribute),
        required=True,
        description="List of attributes assigned to this variant.",
    )
    cost_price = graphene.Field(Money, description="Cost price of the variant.")
    margin = graphene.Int(description="Gross margin percentage value.")
    quantity_ordered = graphene.Int(description="Total quantity ordered.")
    revenue = graphene.Field(
        TaxedMoney,
        period=graphene.Argument(ReportingPeriod),
        description=(
            "Total revenue generated by a variant in given period of time. Note: this "
            "field should be queried using `reportProductSales` query as it uses "
            "optimizations suitable for such calculations."
        ),
    )
    images = graphene.List(
        lambda: ProductImage, description="List of images for the product variant."
    )
    translation = TranslationField(
        ProductVariantTranslation, type_name="product variant"
    )
    digital_content = graphene.Field(
        DigitalContent, description="Digital content for the product variant."
    )

    stocks = graphene.Field(
        graphene.List(Stock),
        description="Stocks for the product variant.",
        country_code=graphene.Argument(
            CountryCodeEnum,
            description="Two-letter ISO 3166-1 country code.",
            required=False,
        ),
    )

    class Meta:
        description = (
            "Represents a version of a product such as different size or color."
        )
        only_fields = ["id", "name", "product", "sku", "track_inventory", "weight"]
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.ProductVariant

    @staticmethod
    def resolve_stocks(root: models.ProductVariant, info, country_code=None):
        if not country_code:
            return root.stocks.annotate_available_quantity().all()
        return root.stocks.annotate_available_quantity().for_country(country_code).all()

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_digital_content(root: models.ProductVariant, *_args):
        return getattr(root, "digital_content", None)

    @staticmethod
    def resolve_stock_quantity(root: models.ProductVariant, info):
        return get_available_quantity_for_customer(root, info.context.country)

    @staticmethod
    def resolve_attributes(root: models.ProductVariant, info):
        return SelectedAttributesByProductVariantIdLoader(info.context).load(root.id)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_margin(root: models.ProductVariant, *_args):
        return get_margin_for_variant(root)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_cost_price(root: models.ProductVariant, *_args):
        return root.cost_price

    @staticmethod
    def resolve_price(root: models.ProductVariant, *_args):
        return root.base_price

    @staticmethod
    def resolve_pricing(root: models.ProductVariant, info):
        context = info.context
        product = ProductByIdLoader(context).load(root.product_id)
        collections = CollectionsByProductIdLoader(context).load(root.product_id)

        def calculate_pricing_info(discounts):
            def calculate_pricing_with_product(product):
                def calculate_pricing_with_collections(collections):
                    availability = get_variant_availability(
                        variant=root,
                        product=product,
                        collections=collections,
                        discounts=discounts,
                        country=context.country,
                        local_currency=context.currency,
                        plugins=context.plugins,
                    )
                    return VariantPricingInfo(**asdict(availability))

                return collections.then(calculate_pricing_with_collections)

            return product.then(calculate_pricing_with_product)

        return (
            DiscountsByDateTimeLoader(context)
            .load(info.context.request_time)
            .then(calculate_pricing_info)
        )

    @staticmethod
    def resolve_product(root: models.ProductVariant, info):
        return ProductByIdLoader(info.context).load(root.product_id)

    @staticmethod
    def resolve_is_available(root: models.ProductVariant, info):
        country = info.context.country
        return is_variant_in_stock(root, country)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_price_override(root: models.ProductVariant, *_args):
        return root.price_override

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_quantity(root: models.ProductVariant, info):
        return get_available_quantity(root, info.context.country)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_quantity_ordered(root: models.ProductVariant, *_args):
        # This field is added through annotation when using the
        # `resolve_report_product_sales` resolver.
        return getattr(root, "quantity_ordered", None)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_quantity_allocated(root: models.ProductVariant, info):
        country = info.context.country
        return get_quantity_allocated(root, country)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_revenue(root: models.ProductVariant, *_args, period):
        start_date = reporting_period_to_date(period)
        return calculate_revenue_for_variant(root, start_date)

    @staticmethod
    def resolve_images(root: models.ProductVariant, *_args):
        return root.images.all()

    @classmethod
    def get_node(cls, info, pk):
        user = info.context.user
        visible_products = models.Product.objects.visible_to_user(user).values_list(
            "pk", flat=True
        )
        qs = cls._meta.model.objects.filter(product__id__in=visible_products)
        return qs.filter(pk=pk).first()

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_private_meta(root: models.ProductVariant, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.ProductVariant, _info):
        return resolve_meta(root, _info)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)


@key(fields="id")
class Product(CountableDjangoObjectType):
    url = graphene.String(
        description="The storefront URL for the product.",
        required=True,
        deprecation_reason="This field will be removed after 2020-07-31.",
    )
    thumbnail = graphene.Field(
        Image,
        description="The main thumbnail for a product.",
        size=graphene.Argument(graphene.Int, description="Size of thumbnail."),
    )
    pricing = graphene.Field(
        ProductPricingInfo,
        description=(
            "Lists the storefront product's pricing, the current price and discounts, "
            "only meant for displaying."
        ),
    )
    is_available = graphene.Boolean(
        description="Whether the product is in stock and visible or not."
    )
    base_price = graphene.Field(Money, description="The product's default base price.")
    minimal_variant_price = graphene.Field(
        Money, description="The price of the cheapest variant (including discounts)."
    )
    tax_type = graphene.Field(
        TaxType, description="A type of tax. Assigned by enabled tax gateway"
    )
    attributes = graphene.List(
        graphene.NonNull(SelectedAttribute),
        required=True,
        description="List of attributes assigned to this product.",
    )
    purchase_cost = graphene.Field(MoneyRange)
    margin = graphene.Field(Margin)
    image_by_id = graphene.Field(
        lambda: ProductImage,
        id=graphene.Argument(graphene.ID, description="ID of a product image."),
        description="Get a single product image by ID.",
    )
    variants = graphene.List(
        ProductVariant, description="List of variants for the product."
    )
    images = graphene.List(
        lambda: ProductImage, description="List of images for the product."
    )
    collections = graphene.List(
        lambda: Collection, description="List of collections for the product."
    )
    translation = TranslationField(ProductTranslation, type_name="product")

    class Meta:
        description = "Represents an individual item for sale in the storefront."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Product
        only_fields = [
            "category",
            "charge_taxes",
            "description",
            "description_json",
            "id",
            "is_published",
            "name",
            "slug",
            "product_type",
            "publication_date",
            "seo_description",
            "seo_title",
            "updated_at",
            "weight",
        ]

    @staticmethod
    def resolve_category(root: models.Product, info):
        category_id = root.category_id
        if category_id is None:
            return None

        return CategoryByIdLoader(info.context).load(category_id)

    @staticmethod
    def resolve_tax_type(root: models.Product, info):
        tax_data = info.context.plugins.get_tax_code_from_object_meta(root)
        return TaxType(tax_code=tax_data.code, description=tax_data.description)

    @staticmethod
    def resolve_thumbnail(root: models.Product, info, *, size=255):
        def return_first_thumbnail(images):
            image = images[0] if images else None
            if image:
                url = get_product_image_thumbnail(image, size, method="thumbnail")
                alt = image.alt
                return Image(alt=alt, url=info.context.build_absolute_uri(url))
            return None

        return (
            ImagesByProductIdLoader(info.context)
            .load(root.id)
            .then(return_first_thumbnail)
        )

    @staticmethod
    def resolve_url(root: models.Product, *_args):
        return ""

    @staticmethod
    def resolve_pricing(root: models.Product, info):
        context = info.context
        variants = ProductVariantsByProductIdLoader(context).load(root.id)
        collections = CollectionsByProductIdLoader(context).load(root.id)

        def calculate_pricing_info(discounts):
            def calculate_pricing_with_variants(variants):
                def calculate_pricing_with_collections(collections):
                    availability = get_product_availability(
                        product=root,
                        variants=variants,
                        collections=collections,
                        discounts=discounts,
                        country=context.country,
                        local_currency=context.currency,
                        plugins=context.plugins,
                    )
                    return ProductPricingInfo(**asdict(availability))

                return collections.then(calculate_pricing_with_collections)

            return variants.then(calculate_pricing_with_variants)

        return (
            DiscountsByDateTimeLoader(context)
            .load(info.context.request_time)
            .then(calculate_pricing_info)
        )

    @staticmethod
    def resolve_is_available(root: models.Product, info):
        country = info.context.country
        in_stock = is_product_in_stock(root, country)
        return root.is_visible and in_stock

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_base_price(root: models.Product, _info):
        return root.price

    @staticmethod
    def resolve_price(root: models.Product, info):
        context = info.context

        def calculate_price(discounts):
            price_range = root.get_price_range(discounts)
            price = info.context.plugins.apply_taxes_to_product(
                root, price_range.start, info.context.country
            )
            return price.net

        return (
            DiscountsByDateTimeLoader(context)
            .load(info.context.request_time)
            .then(calculate_price)
        )

    @staticmethod
    def resolve_attributes(root: models.Product, info):
        return SelectedAttributesByProductIdLoader(info.context).load(root.id)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_purchase_cost(root: models.Product, *_args):
        purchase_cost, _ = get_product_costs_data(root)
        return purchase_cost

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_margin(root: models.Product, *_args):
        _, margin = get_product_costs_data(root)
        return Margin(margin[0], margin[1])

    @staticmethod
    def resolve_image_by_id(root: models.Product, info, id):
        pk = get_database_id(info, id, ProductImage)
        try:
            return root.images.get(pk=pk)
        except models.ProductImage.DoesNotExist:
            raise GraphQLError("Product image not found.")

    @staticmethod
    def resolve_images(root: models.Product, info, **_kwargs):
        return ImagesByProductIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_variants(root: models.Product, info, **_kwargs):
        return ProductVariantsByProductIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_collections(root: models.Product, *_args):
        return root.collections.all()

    @classmethod
    def get_node(cls, info, pk):
        if info.context:
            qs = cls._meta.model.objects.visible_to_user(info.context.user)
            return qs.filter(pk=pk).first()
        return None

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_private_meta(root: models.Product, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.Product, _info):
        return resolve_meta(root, _info)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)


@key(fields="id")
class ProductType(CountableDjangoObjectType):
    products = PrefetchingConnectionField(
        Product, description="List of products of this type."
    )
    tax_rate = TaxRateType(description="A type of tax rate.")
    tax_type = graphene.Field(
        TaxType, description="A type of tax. Assigned by enabled tax gateway"
    )
    variant_attributes = graphene.List(
        Attribute, description="Variant attributes of that product type."
    )
    product_attributes = graphene.List(
        Attribute, description="Product attributes of that product type."
    )
    available_attributes = FilterInputConnectionField(
        Attribute, filter=AttributeFilterInput()
    )

    class Meta:
        description = (
            "Represents a type of product. It defines what attributes are available to "
            "products of this type."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.ProductType
        only_fields = [
            "has_variants",
            "id",
            "is_digital",
            "is_shipping_required",
            "name",
            "slug",
            "weight",
            "tax_type",
        ]

    @staticmethod
    def resolve_tax_type(root: models.ProductType, info):
        tax_data = info.context.plugins.get_tax_code_from_object_meta(root)
        return TaxType(tax_code=tax_data.code, description=tax_data.description)

    @staticmethod
    def resolve_tax_rate(root: models.ProductType, _info, **_kwargs):
        # FIXME this resolver should be dropped after we drop tax_rate from API
        if not hasattr(root, "meta"):
            return None
        return root.get_value_from_metadata("vatlayer.code")

    @staticmethod
    def resolve_product_attributes(root: models.ProductType, *_args, **_kwargs):
        return root.product_attributes.product_attributes_sorted().all()

    @staticmethod
    def resolve_variant_attributes(root: models.ProductType, *_args, **_kwargs):
        return root.variant_attributes.variant_attributes_sorted().all()

    @staticmethod
    def resolve_products(root: models.ProductType, info, **_kwargs):
        return root.products.visible_to_user(info.context.user)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_available_attributes(root: models.ProductType, info, **kwargs):
        qs = models.Attribute.objects.get_unassigned_attributes(root.pk)
        return resolve_attributes(info, qs=qs, **kwargs)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_private_meta(root: models.ProductType, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.ProductType, _info):
        return resolve_meta(root, _info)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)


@key(fields="id")
class Collection(CountableDjangoObjectType):
    products = PrefetchingConnectionField(
        Product, description="List of products in this collection."
    )
    background_image = graphene.Field(
        Image, size=graphene.Int(description="Size of the image.")
    )
    translation = TranslationField(CollectionTranslation, type_name="collection")

    class Meta:
        description = "Represents a collection of products."
        only_fields = [
            "description",
            "description_json",
            "id",
            "is_published",
            "name",
            "publication_date",
            "seo_description",
            "seo_title",
            "slug",
        ]
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Collection

    @staticmethod
    def resolve_background_image(root: models.Collection, info, size=None, **_kwargs):
        if root.background_image:
            return Image.get_adjusted(
                image=root.background_image,
                alt=root.background_image_alt,
                size=size,
                rendition_key_set="background_images",
                info=info,
            )

    @staticmethod
    def resolve_products(root: models.Collection, info, first=None, **kwargs):
        return root.products.collection_sorted(info.context.user)

    @classmethod
    def get_node(cls, info, id):
        if info.context:
            user = info.context.user
            qs = cls._meta.model.objects.visible_to_user(user)
            return qs.filter(id=id).first()
        return None

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_private_meta(root: models.Collection, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.Collection, _info):
        return resolve_meta(root, _info)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)


@key(fields="id")
class Category(CountableDjangoObjectType):
    ancestors = PrefetchingConnectionField(
        lambda: Category, description="List of ancestors of the category."
    )
    products = PrefetchingConnectionField(
        Product, description="List of products in the category."
    )
    url = graphene.String(
        description="The storefront's URL for the category.",
        deprecation_reason="This field will be removed after 2020-07-31.",
    )
    children = PrefetchingConnectionField(
        lambda: Category, description="List of children of the category."
    )
    background_image = graphene.Field(
        Image, size=graphene.Int(description="Size of the image.")
    )
    translation = TranslationField(CategoryTranslation, type_name="category")

    class Meta:
        description = (
            "Represents a single category of products. Categories allow to organize "
            "products in a tree-hierarchies which can be used for navigation in the "
            "storefront."
        )
        only_fields = [
            "description",
            "description_json",
            "id",
            "level",
            "name",
            "parent",
            "seo_description",
            "seo_title",
            "slug",
        ]
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Category

    @staticmethod
    def resolve_ancestors(root: models.Category, info, **_kwargs):
        return root.get_ancestors()

    @staticmethod
    def resolve_background_image(root: models.Category, info, size=None, **_kwargs):
        if root.background_image:
            return Image.get_adjusted(
                image=root.background_image,
                alt=root.background_image_alt,
                size=size,
                rendition_key_set="background_images",
                info=info,
            )

    @staticmethod
    def resolve_children(root: models.Category, info, **_kwargs):
        return root.children.all()

    @staticmethod
    def resolve_url(root: models.Category, _info):
        return ""

    @staticmethod
    def resolve_products(root: models.Category, info, **_kwargs):
        tree = root.get_descendants(include_self=True)
        qs = models.Product.objects.published()
        return qs.filter(category__in=tree)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_private_meta(root: models.Category, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.Category, _info):
        return resolve_meta(root, _info)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)


@key(fields="id")
class ProductImage(CountableDjangoObjectType):
    url = graphene.String(
        required=True,
        description="The URL of the image.",
        size=graphene.Int(description="Size of the image."),
    )

    class Meta:
        description = "Represents a product image."
        only_fields = ["alt", "id", "sort_order"]
        interfaces = [relay.Node]
        model = models.ProductImage

    @staticmethod
    def resolve_url(root: models.ProductImage, info, *, size=None):
        if size:
            url = get_thumbnail(root.image, size, method="thumbnail")
        else:
            url = root.image.url
        return info.context.build_absolute_uri(url)

    @staticmethod
    def __resolve_reference(root, _info, **_kwargs):
        return graphene.Node.get_node_from_global_id(_info, root.id)
