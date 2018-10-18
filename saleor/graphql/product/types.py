import re

import graphene
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql.error import GraphQLError

from ...product import models
from ...product.templatetags.product_images import get_thumbnail
from ...product.utils import products_with_details
from ...product.utils.availability import get_availability
from ...product.utils.costs import (
    get_margin_for_variant, get_product_costs_data)
from ..core.decorators import permission_required
from ..core.types.common import CountableDjangoObjectType
from ..core.types.money import (
    Money, MoneyRange, TaxedMoney, TaxedMoneyRange, TaxRateType)
from ..utils import get_database_id
from .descriptions import AttributeDescriptions, AttributeValueDescriptions
from .filters import ProductFilterSet

COLOR_PATTERN = r'^(#[0-9a-fA-F]{3}|#(?:[0-9a-fA-F]{2}){2,4}|(rgb|hsl)a?\((-?\d+%?[,\s]+){2,3}\s*[\d\.]+%?\))$'  # noqa
color_pattern = re.compile(COLOR_PATTERN)


class AttributeValueType(graphene.Enum):
    COLOR = 'COLOR'
    GRADIENT = 'GRADIENT'
    URL = 'URL'
    STRING = 'STRING'


def resolve_attribute_list(attributes):
    keys = list(attributes.keys())
    values = list(attributes.values())

    attributes_map = {
        att.pk: att for att in models.Attribute.objects.filter(
            pk__in=keys)}
    values_map = {
        val.pk: val for val in models.AttributeValue.objects.filter(
            pk__in=values)}

    attributes_list = [SelectedAttribute(
        attribute=attributes_map.get(int(k)),
        value=values_map.get(int(v)))
        for k, v in attributes.items()]
    return attributes_list


def resolve_attribute_value_type(attribute_value):
    if color_pattern.match(attribute_value):
        return AttributeValueType.COLOR
    if 'gradient(' in attribute_value:
        return AttributeValueType.GRADIENT
    if '://' in attribute_value:
        return AttributeValueType.URL
    return AttributeValueType.STRING


class AttributeValue(CountableDjangoObjectType):
    name = graphene.String(description=AttributeValueDescriptions.NAME)
    slug = graphene.String(description=AttributeValueDescriptions.SLUG)
    type = AttributeValueType(description=AttributeValueDescriptions.TYPE)
    value = graphene.String(description=AttributeValueDescriptions.VALUE)

    class Meta:
        description = 'Represents a value of an attribute.'
        exclude_fields = ['attribute']
        interfaces = [relay.Node]
        model = models.AttributeValue

    def resolve_type(self, info):
        return resolve_attribute_value_type(self.value)


class Attribute(CountableDjangoObjectType):
    name = graphene.String(description=AttributeDescriptions.NAME)
    slug = graphene.String(description=AttributeDescriptions.SLUG)
    values = graphene.List(
        AttributeValue, description=AttributeDescriptions.VALUES)

    class Meta:
        description = """Custom attribute of a product. Attributes can be
        assigned to products and variants at the product type level."""
        exclude_fields = []
        interfaces = [relay.Node]
        filter_fields = ['id', 'slug']
        model = models.Attribute

    def resolve_values(self, info):
        return self.values.all()


class AttributeTypeEnum(graphene.Enum):
    PRODUCT = 'PRODUCT'
    VARIANT = 'VARIANT'


class Margin(graphene.ObjectType):
    start = graphene.Int()
    stop = graphene.Int()


class SelectedAttribute(graphene.ObjectType):
    attribute = graphene.Field(
        Attribute, default_value=None, description=AttributeDescriptions.NAME)
    value = graphene.Field(
        AttributeValue,
        default_value=None, description='Value of an attribute.')

    class Meta:
        description = 'Represents a custom attribute.'


class ProductVariant(CountableDjangoObjectType):
    stock_quantity = graphene.Int(
        required=True, description='Quantity of a product available for sale.')
    price_override = graphene.Field(
        Money,
        description="""Override the base price of a product if necessary.
        A value of `null` indicates that the default product price is used.""")
    price = graphene.Field(Money, description="Price of the product variant.")
    attributes = graphene.List(
        SelectedAttribute,
        description='List of attributes assigned to this variant.')
    cost_price = graphene.Field(
        Money, description='Cost price of the variant.')
    margin = graphene.Int(description='Gross margin percentage value.')

    class Meta:
        description = """Represents a version of a product such as different
        size or color."""
        exclude_fields = ['variant_images']
        interfaces = [relay.Node]
        model = models.ProductVariant
        filter_fields = ['id']

    def resolve_stock_quantity(self, info):
        return self.quantity_available

    def resolve_attributes(self, info):
        return resolve_attribute_list(self.attributes)

    def resolve_margin(self, info):
        return get_margin_for_variant(self)

    def resolve_price(self, info):
        return (
            self.price_override
            if self.price_override is not None else self.product.price)

    @permission_required('product.manage_products')
    def resolve_price_override(self, info):
        return self.price_override


class ProductAvailability(graphene.ObjectType):
    available = graphene.Boolean()
    on_sale = graphene.Boolean()
    discount = graphene.Field(TaxedMoney)
    discount_local_currency = graphene.Field(TaxedMoney)
    price_range = graphene.Field(TaxedMoneyRange)
    price_range_undiscounted = graphene.Field(TaxedMoneyRange)
    price_range_local_currency = graphene.Field(TaxedMoneyRange)

    class Meta:
        description = 'Represents availability of a product in the storefront.'


class Image(graphene.ObjectType):
    url = graphene.String(
        required=True,
        description='The URL of the image.',
        size=graphene.Int(description='Size of the image'))

    class Meta:
        description = 'Represents an image.'

    def resolve_url(self, info, size=None):
        if size:
            return get_thumbnail(self, size, method='thumbnail')
        return self.url


class Product(CountableDjangoObjectType):
    url = graphene.String(
        description='The storefront URL for the product.', required=True)
    thumbnail_url = graphene.String(
        description='The URL of a main thumbnail for a product.',
        size=graphene.Argument(graphene.Int, description='Size of thumbnail'))
    availability = graphene.Field(
        ProductAvailability,
        description="""Informs about product's availability in the storefront,
        current price and discounts.""")
    price = graphene.Field(
        Money,
        description="""The product's base price (without any discounts
        applied).""")
    attributes = graphene.List(
        SelectedAttribute,
        description='List of attributes assigned to this product.')
    purchase_cost = graphene.Field(MoneyRange)
    margin = graphene.Field(Margin)
    image_by_id = graphene.Field(
        lambda: ProductImage,
        id=graphene.Argument(
            graphene.ID, description='ID of a product image.'),
        description='Get a single product image by ID')

    class Meta:
        description = """Represents an individual item for sale in the
        storefront."""
        interfaces = [relay.Node]
        model = models.Product

    def resolve_thumbnail_url(self, info, *, size=None):
        if not size:
            size = 255
        return get_thumbnail(self.get_first_image(), size, method='thumbnail')

    def resolve_url(self, info):
        return self.get_absolute_url()

    def resolve_availability(self, info):
        context = info.context
        availability = get_availability(
            self, context.discounts, context.taxes, context.currency)
        return ProductAvailability(**availability._asdict())

    def resolve_attributes(self, info):
        return resolve_attribute_list(self.attributes)

    def resolve_product_type(self, info):
        return self.product_type

    @permission_required('product.manage_products')
    def resolve_purchase_cost(self, info):
        purchase_cost, _ = get_product_costs_data(self)
        return purchase_cost

    @permission_required('product.manage_products')
    def resolve_margin(self, info):
        _, margin = get_product_costs_data(self)
        return Margin(margin[0], margin[1])

    def resolve_image_by_id(self, info, id):
        pk = get_database_id(info, id, ProductImage)
        try:
            return self.images.get(pk=pk)
        except models.ProductImage.DoesNotExist:
            raise GraphQLError('Product image not found.')


class ProductType(CountableDjangoObjectType):
    products = DjangoFilterConnectionField(
        Product,
        filterset_class=ProductFilterSet,
        description='List of products of this type.')
    tax_rate = TaxRateType(description='A type of tax rate.')
    variant_attributes = graphene.List(
        Attribute, description='Variant attributes of that product type.')
    product_attributes = graphene.List(
        Attribute, description='Product attributes of that product type.')

    class Meta:
        description = """Represents a type of product. It defines what
        attributes are available to products of this type."""
        interfaces = [relay.Node]
        model = models.ProductType
        filter_fields = ['id']

    def resolve_products(self, info, **kwargs):
        user = info.context.user
        return products_with_details(
            user=user).filter(product_type=self).distinct()

    def resolve_variant_attributes(self, info):
        return self.variant_attributes.prefetch_related('values')

    def resolve_product_attributes(self, info):
        return self.product_attributes.prefetch_related('values')


class Collection(CountableDjangoObjectType):
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilterSet,
        description='List of collection products.')
    background_image = graphene.Field(Image)

    class Meta:
        description = "Represents a collection of products."
        exclude_fields = ['voucher_set', 'sale_set', 'menuitem_set']
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith']}
        interfaces = [relay.Node]
        model = models.Collection

    def resolve_products(self, info, **kwargs):
        user = info.context.user
        return products_with_details(
            user=user).filter(collections=self).distinct()


class Category(CountableDjangoObjectType):
    products = DjangoFilterConnectionField(
        Product,
        filterset_class=ProductFilterSet,
        description='List of products in the category.')
    url = graphene.String(
        description='The storefront\'s URL for the category.')
    ancestors = DjangoFilterConnectionField(
        lambda: Category,
        description='List of ancestors of the category.')
    children = DjangoFilterConnectionField(
        lambda: Category,
        description='List of children of the category.')
    background_image = graphene.Field(Image)

    class Meta:
        description = """Represents a single category of products. Categories
        allow to organize products in a tree-hierarchies which can be used for
        navigation in the storefront."""
        exclude_fields = [
            'lft', 'rght', 'tree_id', 'voucher_set', 'sale_set',
            'menuitem_set']
        interfaces = [relay.Node]
        filter_fields = ['id', 'name']
        model = models.Category

    def resolve_ancestors(self, info, **kwargs):
        return self.get_ancestors().distinct()

    def resolve_children(self, info, **kwargs):
        return self.children.distinct()

    def resolve_url(self, info):
        return self.get_absolute_url()

    def resolve_products(self, info, **kwargs):
        qs = models.Product.objects.available_products().prefetch_related(
            'variants', 'images', 'product_type')
        categories_tree = self.get_descendants(include_self=True)
        qs = qs.filter(category__in=categories_tree)
        return qs.distinct()


class ProductImage(CountableDjangoObjectType):
    url = graphene.String(
        required=True,
        description='The URL of the image.',
        size=graphene.Int(description='Size of the image'))

    class Meta:
        description = 'Represents a product image.'
        exclude_fields = [
            'image', 'product', 'ppoi', 'productvariant_set',
            'variant_images']
        interfaces = [relay.Node]
        model = models.ProductImage

    def resolve_url(self, info, *, size=None):
        if size:
            return get_thumbnail(self.image, size, method='thumbnail')
        return self.image.url
