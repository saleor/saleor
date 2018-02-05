import functools
import operator

from django.db.models import Q
import graphene
from graphene import relay
from graphene_django import DjangoConnectionField, DjangoObjectType

from ...product.models import (
    AttributeChoiceValue, Category, Product, ProductAttribute, ProductImage,
    ProductVariant)
from ...product.templatetags.product_images import product_first_image
from ...product.utils import get_availability, products_visible_to_user
from ..core.types import PriceRangeType, PriceType
from ..utils import CategoryAncestorsCache, DjangoPkInterface
from .scalars import AttributesFilterScalar

CONTEXT_CACHE_NAME = '__cache__'
CACHE_ANCESTORS = 'ancestors'


def get_ancestors_from_cache(category, context):
    cache = getattr(context, CONTEXT_CACHE_NAME, None)
    if cache and CACHE_ANCESTORS in cache:
        return cache[CACHE_ANCESTORS].get(category)
    return category.get_ancestors()


class ProductAvailabilityType(graphene.ObjectType):
    available = graphene.Boolean()
    on_sale = graphene.Boolean()
    discount = graphene.Field(lambda: PriceType)
    discount_local_currency = graphene.Field(lambda: PriceType)
    price_range = graphene.Field(lambda: PriceRangeType)
    price_range_undiscounted = graphene.Field(lambda: PriceRangeType)
    price_range_local_currency = graphene.Field(lambda: PriceRangeType)


class ProductType(DjangoObjectType):
    url = graphene.String()
    thumbnail_url = graphene.String(
        size=graphene.Argument(
            graphene.String,
            description="The size of a thumbnail, for example 255x255"))
    images = graphene.List(lambda: ProductImageType)
    variants = graphene.List(lambda: ProductVariantType)
    availability = graphene.Field(lambda: ProductAvailabilityType)
    price = graphene.Field(lambda: PriceType)

    class Meta:
        model = Product
        interfaces = (relay.Node, DjangoPkInterface)

    def resolve_thumbnail_url(self, info, **args):
        size = args.get('size')
        if not size:
            size = '255x255'
        return product_first_image(self, size)

    def resolve_images(self, info):
        return self.images.all()

    def resolve_variants(self, info):
        return self.variants.all()

    def resolve_url(self, info):
        return self.get_absolute_url()

    def resolve_availability(self, info):
        context = info.context
        a = get_availability(self, context.discounts, context.currency)
        return ProductAvailabilityType(**a._asdict())


class CategoryType(DjangoObjectType):
    products = DjangoConnectionField(
        ProductType,
        attributes=graphene.Argument(
            graphene.List(AttributesFilterScalar),
            description="""A list of attribute:value pairs to filter
                the products by"""),
        order_by=graphene.Argument(
            graphene.String,
            description="""A name of field to sort the products by. The negative
                sign in front of name implies descending order."""),
        price_lte=graphene.Argument(
            graphene.Float, description="""Get the products with price lower
                than or equal to the given value"""),
        price_gte=graphene.Argument(
            graphene.Float, description="""Get the products with price greater
                than or equal to the given value"""))
    products_count = graphene.Int()
    url = graphene.String()
    ancestors = graphene.List(lambda: CategoryType)
    children = graphene.List(lambda: CategoryType)
    siblings = graphene.List(lambda: CategoryType)

    class Meta:
        model = Category
        interfaces = (relay.Node, DjangoPkInterface)

    def resolve_ancestors(self, info):
        return get_ancestors_from_cache(self, info.context)

    def resolve_children(self, info):
        return self.children.all()

    def resolve_siblings(self, info):
        return self.get_siblings()

    def resolve_products_count(self, info):
        return self.products.count()

    def resolve_url(self, info):
        ancestors = get_ancestors_from_cache(self, info.context)
        return self.get_absolute_url(ancestors)

    def resolve_products(self, info, **args):
        context = info.context
        qs = products_visible_to_user(context.user)
        qs = qs.prefetch_related('images', 'category', 'variants__stock')
        qs = qs.filter(category=self)

        attributes_filter, order_by, price_lte, price_gte = map(
            args.get, ['attributes', 'order_by', 'price_lte', 'price_gte'])

        if attributes_filter:
            attributes = ProductAttribute.objects.prefetch_related('values')
            attributes_map = {attribute.slug: attribute.pk
                              for attribute in attributes}
            values_map = {attr.slug: {value.slug: value.pk
                                      for value in attr.values.all()}
                          for attr in attributes}
            queries = {}
            # Convert attribute:value pairs into a dictionary where
            # attributes are keys and values are grouped in lists
            for attr_name, val_slug in attributes_filter:
                try:
                    attr_pk = attributes_map[attr_name]
                except KeyError:
                    attr_pk = None
                else:
                    try:
                        attr_val_pk = values_map[attr_name][val_slug]
                    except KeyError:
                        attr_val_pk = None
                    else:
                        if attr_val_pk is not None and attr_pk not in queries:
                            queries[attr_pk] = [attr_val_pk]
                        else:
                            queries[attr_pk].append(attr_val_pk)
            if queries:
                # Combine filters of the same attribute with OR operator
                # and then combine full query with AND operator.
                combine_and = [functools.reduce(operator.or_, [
                    Q(**{'variants__attributes__%s' % key: v}) |
                    Q(**{'attributes__%s' % key: v})
                    for v in values]) for key, values in queries.items()]
                query = functools.reduce(operator.and_, combine_and)
                qs = qs.filter(query).distinct()

        if order_by:
            qs = qs.order_by(order_by)

        def filter_by_price(queryset, value, operator):
            return [
                obj for obj in queryset
                if operator(
                    get_availability(obj, context.discounts)
                    .price_range.min_price.gross, value)
            ]

        if price_lte:
            qs = filter_by_price(qs, price_lte, operator.le)

        if price_gte:
            qs = filter_by_price(qs, price_gte, operator.ge)
        return qs


class ProductVariantType(DjangoObjectType):
    stock_quantity = graphene.Int()
    price_override = graphene.Field(lambda: PriceType)

    class Meta:
        model = ProductVariant
        interfaces = (relay.Node, DjangoPkInterface)

    def resolve_stock_quantity(self, info):
        return self.get_stock_quantity()


class ProductImageType(DjangoObjectType):
    url = graphene.String(size=graphene.String())

    class Meta:
        model = ProductImage
        interfaces = (relay.Node, DjangoPkInterface)

    def resolve_url(self, info, **args):
        size = args.get('size')
        if size:
            return self.image.crop[size].url
        return self.image.url


class ProductAttributeValue(DjangoObjectType):
    class Meta:
        model = AttributeChoiceValue
        interfaces = (relay.Node, DjangoPkInterface)


class ProductAttributeType(DjangoObjectType):
    values = graphene.List(lambda: ProductAttributeValue)

    class Meta:
        model = ProductAttribute
        interfaces = (relay.Node, DjangoPkInterface)

    def resolve_values(self, info):
        return self.values.all()


def resolve_category(pk, info):
    categories = Category.tree.filter(pk=pk).get_cached_trees()
    if categories:
        category = categories[0]
        cache = {CACHE_ANCESTORS: CategoryAncestorsCache(category)}
        setattr(info.context, CONTEXT_CACHE_NAME, cache)
        return category
    return None


def resolve_attributes(category_pk):
    queryset = ProductAttribute.objects.prefetch_related('values')
    if category_pk:
        # Get attributes that are used with product types
        # within the given category.
        tree = Category.objects.get(
            pk=category_pk).get_descendants(include_self=True)
        product_types = set(
            [obj[0] for obj in Product.objects.filter(
                category__in=tree).values_list('product_type_id')])
        queryset = queryset.filter(
            Q(product_types__in=product_types) |
            Q(product_variant_types__in=product_types))
    return queryset.distinct()
