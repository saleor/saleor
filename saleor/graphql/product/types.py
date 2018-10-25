import re

import graphene
import graphene_django_optimizer as gql_optimizer
from django.db.models import Prefetch
from graphene import relay
from graphql.error import GraphQLError

from ...product import models
from ...product.templatetags.product_images import get_thumbnail
from ...product.utils import calculate_revenue_for_variant
from ...product.utils.availability import get_availability
from ...product.utils.costs import (
    get_margin_for_variant, get_product_costs_data)
from ..core.decorators import permission_required
from ..core.fields import PrefetchingConnectionField
from ..core.types import (
    CountableDjangoObjectType, Money, MoneyRange, ReportingPeriod, TaxedMoney,
    TaxedMoneyRange, TaxRateType)
from ..utils import get_database_id, reporting_period_to_date
from .filters import (
    filter_products_by_attributes, filter_products_by_price, sort_qs)
from .descriptions import AttributeDescriptions, AttributeValueDescriptions
from .scalars import AttributeScalar

COLOR_PATTERN = r'^(#[0-9a-fA-F]{3}|#(?:[0-9a-fA-F]{2}){2,4}|(rgb|hsl)a?\((-?\d+%?[,\s]+){2,3}\s*[\d\.]+%?\))$'  # noqa
color_pattern = re.compile(COLOR_PATTERN)


class AttributeTypeEnum(graphene.Enum):
    PRODUCT = 'PRODUCT'
    VARIANT = 'VARIANT'


class AttributeValueType(graphene.Enum):
    COLOR = 'COLOR'
    GRADIENT = 'GRADIENT'
    URL = 'URL'
    STRING = 'STRING'


class StockAvailability(graphene.Enum):
    IN_STOCK = 'AVAILABLE'
    OUT_OF_STOCK = 'OUT_OF_STOCK'


def resolve_attribute_list(attributes_hstore, attributes_qs):
    """Resolve attributes dict into a list of `SelectedAttribute`s.
    keys = list(attributes.keys())
    values = list(attributes.values())

    `attributes_qs` is the queryset of attribute objects. If it's prefetch
    beforehand along with the values, it saves database queries.
    """
    attributes_map = {}
    values_map = {}
    for attr in attributes_qs:
        attributes_map[attr.pk] = attr
        for val in attr.values.all():
            values_map[val.pk] = val

    attributes_list = [SelectedAttribute(
        attribute=attributes_map.get(int(k)),
        value=values_map.get(int(v)))
        for k, v in attributes_hstore.items()]
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
    values = gql_optimizer.field(
        graphene.List(
            AttributeValue, description=AttributeDescriptions.VALUES),
        model_field='values')

    class Meta:
        description = """Custom attribute of a product. Attributes can be
        assigned to products and variants at the product type level."""
        exclude_fields = []
        interfaces = [relay.Node]
        model = models.Attribute

    def resolve_values(self, info):
        return self.values.all()


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
    quantity_ordered = graphene.Int(description='Total quantity ordered.')
    revenue = graphene.Field(
        TaxedMoney, period=graphene.Argument(ReportingPeriod),
        description='''Total revenue generated by a variant in given period of
        time. Note: this field should be queried using `reportProductSales`
        query as it uses optimizations suitable for such calculations.''')

    class Meta:
        description = """Represents a version of a product such as different
        size or color."""
        exclude_fields = ['variant_images']
        interfaces = [relay.Node]
        model = models.ProductVariant

    def resolve_stock_quantity(self, info):
        return self.quantity_available

    @gql_optimizer.resolver_hints(
        prefetch_related='product__product_type__variant_attributes__values')
    def resolve_attributes(self, info):
        attributes_qs = self.product.product_type.variant_attributes.all()
        return resolve_attribute_list(self.attributes, attributes_qs)

    def resolve_margin(self, info):
        return get_margin_for_variant(self)

    def resolve_price(self, info):
        return (
            self.price_override
            if self.price_override is not None else self.product.price)

    @permission_required('product.manage_products')
    def resolve_price_override(self, info):
        return self.price_override

    def resolve_quantity_ordered(self, info):
        # This field is added through annotation when using the
        # `resolve_report_product_sales` resolver.
        return getattr(self, 'quantity_ordered', None)

    def resolve_revenue(self, info, period):
        start_date = reporting_period_to_date(period)
        return calculate_revenue_for_variant(self, start_date)


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
    variants = gql_optimizer.field(
        PrefetchingConnectionField(ProductVariant), model_field='variants')
    images = gql_optimizer.field(
        PrefetchingConnectionField(lambda: ProductImage), model_field='images')

    class Meta:
        description = """Represents an individual item for sale in the
        storefront."""
        interfaces = [relay.Node]
        model = models.Product

    @gql_optimizer.resolver_hints(prefetch_related='images')
    def resolve_thumbnail_url(self, info, *, size=None):
        if not size:
            size = 255
        return get_thumbnail(self.get_first_image(), size, method='thumbnail')

    def resolve_url(self, info):
        return self.get_absolute_url()

    @gql_optimizer.resolver_hints(
            prefetch_related='variants',
            only=['available_on', 'charge_taxes', 'price', 'tax_rate'])
    def resolve_availability(self, info):
        context = info.context
        availability = get_availability(
            self, context.discounts, context.taxes, context.currency)
        return ProductAvailability(**availability._asdict())

    @gql_optimizer.resolver_hints(
            prefetch_related='product_type__product_attributes__values')
    def resolve_attributes(self, info):
        attributes_qs = self.product_type.product_attributes.all()
        return resolve_attribute_list(self.attributes, attributes_qs)

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

    @gql_optimizer.resolver_hints(model_field='images')
    def resolve_images(self, info, **kwargs):
        return self.images.all()

    def resolve_variants(self, info, **kwargs):
        return self.variants.all()


def prefetch_products(info, *args, **kwargs):
    """Prefetch products visible to the current user.

    Can be used with models that have the `products` relationship. Queryset of
    products being prefetched is filtered based on permissions of the viewing
    user, to restrict access to unpublished products to non-staff users.
    """
    user = info.context.user
    qs = models.Product.objects.visible_to_user(user)
    return Prefetch(
        'products', queryset=gql_optimizer.query(qs, info),
        to_attr='prefetched_products')


class ProductType(CountableDjangoObjectType):
    products = gql_optimizer.field(
        PrefetchingConnectionField(
            Product, description='List of products of this type.'),
        prefetch_related=prefetch_products)
    product_attributes = gql_optimizer.field(
        PrefetchingConnectionField(Attribute),
        model_field='product_attributes')
    variant_attributes = gql_optimizer.field(
        PrefetchingConnectionField(Attribute),
        model_field='variant_attributes')
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

    def resolve_product_attributes(self, info, **kwargs):
        return self.product_attributes.all()

    def resolve_variant_attributes(self, info, **kwargs):
        return self.variant_attributes.all()

    def resolve_products(self, info, **kwargs):
        if hasattr(self, 'prefetched_products'):
            return self.prefetched_products
        qs = self.products.visible_to_user(info.context.user)
        return gql_optimizer.query(qs, info)


class Collection(CountableDjangoObjectType):
    products = gql_optimizer.field(
        PrefetchingConnectionField(
            Product, description='List of products in this collection.'),
        prefetch_related=prefetch_products)
    background_image = graphene.Field(Image)

    class Meta:
        description = "Represents a collection of products."
        exclude_fields = ['voucher_set', 'sale_set', 'menuitem_set']
        interfaces = [relay.Node]
        model = models.Collection

    def resolve_background_image(self, info, **kwargs):
        return self.background_image or None

    def resolve_products(self, info, **kwargs):
        if hasattr(self, 'prefetched_products'):
            return self.prefetched_products
        qs = self.products.visible_to_user(info.context.user)
        return gql_optimizer.query(qs, info)


class Category(CountableDjangoObjectType):
    products = gql_optimizer.field(
        PrefetchingConnectionField(
            Product, description='List of products in the category.'),
        prefetch_related=prefetch_products)
    url = graphene.String(
        description='The storefront\'s URL for the category.')
    ancestors = PrefetchingConnectionField(
        lambda: Category,
        description='List of ancestors of the category.')
    children = PrefetchingConnectionField(
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
        model = models.Category

    def resolve_ancestors(self, info, **kwargs):
        qs = self.get_ancestors()
        return gql_optimizer.query(qs, info)

    def resolve_background_image(self, info, **kwargs):
        return self.background_image or None

    def resolve_children(self, info, **kwargs):
        qs = self.children.all()
        return gql_optimizer.query(qs, info)

    def resolve_url(self, info):
        return self.get_absolute_url()

    def resolve_products(self, info, **kwargs):
        # If the category has no children, we use the prefetched data.
        children = self.children.all()
        if not children and hasattr(self, 'prefetched_products'):
            return self.prefetched_products

        # Otherwise we want to include products from child categories which
        # requires performing additional logic.
        tree = self.get_descendants(include_self=True)
        qs = models.Product.objects.available_products()
        qs = qs.filter(category__in=tree)
        return gql_optimizer.query(qs, info)


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
