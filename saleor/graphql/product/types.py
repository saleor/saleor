import graphene
from django.db.models import Q
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField

from ...product import models
from ...product.templatetags.product_images import product_first_image
from ...product.utils import (
    get_availability, get_product_costs_data, products_visible_to_user)
from ..core.decorators import permission_required
from ..core.filters import DistinctFilterSet
from ..core.types import (
    CountableDjangoObjectType, Money, TaxedMoney, TaxedMoneyRange)
from ..utils import get_node
from .filters import ProductFilterSet


class GrossMargin(graphene.ObjectType):
    start = graphene.Int()
    stop = graphene.Int()


class SelectedAttribute(graphene.ObjectType):
    name = graphene.String(
        default_value=None,
        description='Name of an attribute')
    value = graphene.String(
        default_value=None,
        description='Value of an attribute.')

    class Meta:
        description = 'Represents a custom product attribute.'


class ProductVariant(CountableDjangoObjectType):
    stock_quantity = graphene.Int(
        required=True,
        description='Quantity of a product available for sale.')
    price_override = graphene.Field(
        Money,
        description="""Override the base price of a product if necessary.
        A value of `null` indicates the the default product price is used.""")
    attributes = graphene.List(
        SelectedAttribute,
        description='List of attributes assigned to this variant.')

    class Meta:
        description = """Represents a version of a product such as different
        size or color."""
        interfaces = [relay.Node]
        model = models.ProductVariant

    def resolve_stock_quantity(self, info):
        return self.get_stock_quantity()

    def resolve_attributes(self, info):
        return resolve_attribute_list(self.attributes)


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


class Product(CountableDjangoObjectType):
    url = graphene.String(
        description='The storefront URL for the product.',
        required=True)
    thumbnail_url = graphene.String(
        description='The URL of a main thumbnail for a product.',
        size=graphene.Argument(
            graphene.String,
            description='Size of a thumbnail, for example 255x255.'))
    # TODO: drop this field in favor of particular ones?
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
        description='List of product attributes assigned to this product.')
    purchase_cost = graphene.Field(TaxedMoneyRange)
    gross_margin = graphene.List(GrossMargin)
    price_range = graphene.Field(TaxedMoneyRange)
    price_range_undiscounted = graphene.Field(TaxedMoneyRange)

    class Meta:
        description = """Represents an individual item for sale in the
        storefront."""
        interfaces = [relay.Node]
        model = models.Product

    def resolve_thumbnail_url(self, info, *, size=None):
        if not size:
            size = '255x255'
        return product_first_image(self, size)

    def resolve_url(self, info):
        return self.get_absolute_url()

    def resolve_availability(self, info):
        context = info.context
        availability = get_availability(
            self, context.discounts, context.currency)
        return ProductAvailability(**availability._asdict())

    def resolve_attributes(self, info):
        return resolve_attribute_list(self.attributes)

    @permission_required(('product.view_product'))
    def resolve_purchase_cost(self, info):
        purchase_cost, _ = get_product_costs_data(self)
        return purchase_cost

    @permission_required('product.view_product')
    def resolve_gross_margin(self, info):
        _, gross_margin = get_product_costs_data(self)
        return [GrossMargin(gross_margin[0], gross_margin[1])]

    def resolve_price_range(self, info):
        context = info.context
        return self.get_price_range(discounts=context.discounts)

    def resolve_price_range_undiscounted(self, info):
        return self.get_price_range()


class ProductType(CountableDjangoObjectType):
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilterSet,
        description='List of products of this type.')

    class Meta:
        description = """Represents a type of product. It defines what
        attributes are available to products of this type."""
        interfaces = [relay.Node]
        model = models.ProductType


class Category(CountableDjangoObjectType):
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilterSet,
        description='List of products in the category.')
    url = graphene.String(
        description='The storefront\'s URL for the category.')
    ancestors = DjangoFilterConnectionField(
        lambda: Category, filterset_class=DistinctFilterSet,
        description='List of ancestors of the category.')
    children = DjangoFilterConnectionField(
        lambda: Category, filterset_class=DistinctFilterSet,
        description='List of children of the category.')

    class Meta:
        description = """Represents a single category of products. Categories
        allow to organize products in a tree-hierarchies which can be used for
        navigation in the storefront."""
        exclude_fields = ['lft', 'rght', 'tree_id']
        interfaces = [relay.Node]
        filter_fields = ['id', 'name']
        model = models.Category

    def resolve_ancestors(self, info, **kwargs):
        return self.get_ancestors().distinct()

    def resolve_children(self, info, **kwargs):
        return self.children.distinct()

    def resolve_url(self, info):
        ancestors = self.get_ancestors().distinct()
        return self.get_absolute_url(ancestors)

    def resolve_products(self, info, **kwargs):
        qs = models.Product.objects.available_products()
        qs = qs.filter(category=self)
        return qs.distinct()


class ProductImage(CountableDjangoObjectType):
    url = graphene.String(
        required=True, description='',
        size=graphene.String(
            description='Size of an image, for example 255x255.'))

    class Meta:
        description = 'Represents a product image.'
        exclude_fields = ['product', 'productvariant_set', 'variant_images']
        interfaces = [relay.Node]
        model = models.ProductImage

    def resolve_url(self, info, *, size=None):
        if size:
            return self.image.crop[size].url
        return self.image.url


class ProductAttributeValue(CountableDjangoObjectType):
    class Meta:
        description = 'Represents a value of an attribute.'
        exclude_fields = ['attribute']
        interfaces = [relay.Node]
        model = models.AttributeChoiceValue


class ProductAttribute(CountableDjangoObjectType):
    values = graphene.List(
        ProductAttributeValue, description='List of attribute\'s values.')

    class Meta:
        description = """Custom attribute of a product. Attributes can be
        dynamically assigned to products and variants at the product type
        level."""
        exclude_fields = ['product_types', 'product_variant_types']
        interfaces = [relay.Node]
        filter_fields = ['id', 'slug']
        model = models.ProductAttribute

    def resolve_values(self, info):
        return self.values.all()


def resolve_attribute_list(attributes=None):
    """
    :param attributes: dict
    :return: list of objects of type SelectedAttribute
    """
    attribute_list = []
    if attributes:
        product_attributes = dict(
            models.ProductAttribute.objects.values_list('id', 'slug'))
        attribute_values = dict(
            models.AttributeChoiceValue.objects.values_list('id', 'slug'))
        for k, v in attributes.items():
            value = None
            name = product_attributes.get(int(k))
            if v:
                value = attribute_values.get(int(v))
            attribute_list.append(SelectedAttribute(name=name, value=value))
    return attribute_list


def resolve_categories(info, level=None):
    qs = models.Category.objects.all()
    if level is not None:
        qs = qs.filter(level=level)
    return qs.distinct()


def resolve_products(info, category_id):
    user = info.context.user
    products = products_visible_to_user(user=user).distinct()
    if category_id is not None:
        category = get_node(info, category_id, only_type=Category)
        return products.filter(category=category)
    return products


def resolve_attributes(category_id, info):
    queryset = models.ProductAttribute.objects.prefetch_related('values')
    if category_id:
        # Get attributes that are used with product types
        # within the given category.
        category = get_node(info, category_id, only_type=Category)
        if category is None:
            return queryset.none()
        tree = category.get_descendants(include_self=True)
        product_types = {
            obj[0]
            for obj in models.Product.objects.filter(
                category__in=tree).values_list('product_type_id')}
        queryset = queryset.filter(
            Q(product_types__in=product_types)
            | Q(product_variant_types__in=product_types))
    return queryset.distinct()
