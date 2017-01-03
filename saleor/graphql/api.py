import graphene
import operator

from django.db.models import Q
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.debug import DjangoDebug

from ..product.models import (AttributeChoiceValue, Category, Product,
                              ProductAttribute, ProductImage, ProductVariant)
from ..product.utils import get_availability
from .scalars import AttributesFilterScalar
from .utils import DjangoPkInterface, connection_with_count, get_object_or_none


class ProductAvailabilityType(graphene.ObjectType):
    available = graphene.Boolean()
    discount = graphene.Field(lambda: PriceType)
    discount_local_currency = graphene.Field(lambda: PriceType)
    price_range = graphene.Field(lambda: PriceRangeType)
    price_range_undiscounted = graphene.Field(lambda: PriceRangeType)
    price_range_local_currency = graphene.Field(lambda: PriceRangeType)


class ProductType(DjangoObjectType):
    url = graphene.String()
    image_url = graphene.String()
    images = graphene.List(lambda: ProductImageType)
    variants = graphene.List(lambda: ProductVariantType)
    availability = graphene.Field(lambda: ProductAvailabilityType)

    class Meta:
        model = Product
        interfaces = (relay.Node, DjangoPkInterface)

    def resolve_image_url(self, args, context, info):
        image = self.images.first()
        return image.image.crop['400x400'].url if image else None

    def resolve_images(self, args, context, info):
        return self.images.all()

    def resolve_variants(self, args, context, info):
        return self.variants.all()

    def resolve_url(self, args, context, info):
        return self.get_absolute_url()

    def resolve_availability(self, args, context, info):
        a = get_availability(self, context.discounts, context.currency)
        return ProductAvailabilityType(**a._asdict())


ProductType.Connection = connection_with_count(ProductType)


class CategoryType(DjangoObjectType):
    products = relay.ConnectionField(
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

    def resolve_ancestors(self, args, context, info):
        return self.get_ancestors()

    def resolve_children(self, args, context, info):
        return self.children.all()

    def resolve_siblings(self, args, context, info):
        return self.get_siblings()

    def resolve_products(self, args, context, info):

        def filter_by_price(queryset, value, operator):
            return [obj for obj in queryset if operator(get_availability(
                obj, context.discounts).price_range.min_price.gross, value)]

        tree = self.get_descendants(include_self=True)
        qs = Product.objects.prefetch_for_api().filter(categories__in=tree)
        attributes_filter = args.get('attributes')
        order_by = args.get('order_by')
        price_lte = args.get('price_lte')
        price_gte = args.get('price_gte')

        if attributes_filter:
            attributes = ProductAttribute.objects.prefetch_related('values')
            attributes_map = {attribute.name: attribute.pk
                              for attribute in attributes}
            values_map = {attr.name: {value.slug: value.pk
                                      for value in attr.values.all()}
                          for attr in attributes}
            queries = {}
            # Convert attribute:value pairs into a dictionary where
            # attributes are keys and values are grouped in lists
            for attr_name, val_slug in attributes_filter:
                try:
                    attr_pk = attributes_map[attr_name]
                except KeyError:
                    raise ValueError("Invalid attribute name: %s" % attr_name)
                else:
                    try:
                        attr_val_pk = values_map[attr_name][val_slug]
                    except KeyError:
                        raise ValueError("Invalid attribute value: %s" %
                                         val_slug)
                    else:
                        if attr_pk not in queries:
                            queries[attr_pk] = [attr_val_pk]
                        else:
                            queries[attr_pk].append(attr_val_pk)
            if queries:
                # Combine filters of the same attribute with OR operator
                # and then combine full query with AND operator.
                combine_and = [reduce(operator.or_, [
                    Q(**{'variants__attributes__%s' % key: v}) |
                    Q(**{'attributes__%s' % key: v})
                    for v in values]) for key, values in queries.items()]
                query = reduce(operator.and_, combine_and)
                qs = qs.filter(query).distinct()

        if order_by:
            qs = qs.order_by(order_by)

        if price_lte:
            qs = filter_by_price(qs, price_lte, operator.le)

        if price_gte:
            qs = filter_by_price(qs, price_gte, operator.ge)
        return qs

    def resolve_products_count(self, args, context, info):
        return self.products.count()

    def resolve_url(self, args, context, info):
        return self.get_absolute_url()


class ProductVariantType(DjangoObjectType):
    stock_quantity = graphene.Int()
    price_override = graphene.Field(lambda: PriceType)

    class Meta:
        model = ProductVariant
        interfaces = (relay.Node, DjangoPkInterface)

    def resolve_stock_quantity(self, args, context, info):
        return self.get_stock_quantity()


class ProductImageType(DjangoObjectType):
    url = graphene.String(size=graphene.String())

    class Meta:
        model = ProductImage
        interfaces = (relay.Node, DjangoPkInterface)

    def resolve_url(self, args, context, info):
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

    def resolve_values(self, args, context, info):
        return self.values.all()


class PriceType(graphene.ObjectType):
    gross = graphene.Float()
    net = graphene.Float()
    currency = graphene.String()


class PriceRangeType(graphene.ObjectType):
    maxPrice = graphene.Field(lambda: PriceType)
    min_price = graphene.Field(lambda: PriceType)


class Viewer(graphene.ObjectType):
    category = graphene.Field(
        CategoryType,
        pk=graphene.Argument(graphene.Int, required=True))
    attributes = graphene.List(
        ProductAttributeType,
        category_pk=graphene.Argument(graphene.Int, required=False))
    debug = graphene.Field(DjangoDebug, name='__debug')

    def resolve_category(self, args, context, info):
        return get_object_or_none(Category, pk=args.get('pk'))

    def resolve_attributes(self, args, context, info):
        category_pk = args.get('category_pk')
        queryset = ProductAttribute.objects.prefetch_related('values')
        if category_pk:
            # Get attributes that are used with product classes
            # within the given category.
            tree = Category.objects.get(
                pk=category_pk).get_descendants(include_self=True)
            product_classes = set(
                [obj[0] for obj in Product.objects.filter(
                    categories__in=tree).values_list('product_class_id')])
            queryset = queryset.filter(
                Q(products_class__in=product_classes) |
                Q(product_variants_class__in=product_classes))
        return queryset.distinct()


class Query(graphene.ObjectType):
    viewer = graphene.Field(Viewer)
    node = relay.Node.Field()

    def resolve_viewer(self, args, context, info):
        return Viewer()


schema = graphene.Schema(Query)
