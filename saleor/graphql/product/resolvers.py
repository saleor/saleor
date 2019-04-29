import graphene
import graphene_django_optimizer as gql_optimizer
from django.db.models import Q, Sum

from ...order import OrderStatus
from ...product import models
from ...search.backends import picker
from ..utils import (
    filter_by_period, filter_by_query_param, get_database_id, get_nodes)
from .filters import (
    filter_products_by_attributes, filter_products_by_categories,
    filter_products_by_collections, filter_products_by_price,
    filter_products_by_stock_availability, sort_qs)
from .types import Category, Collection, ProductVariant

PRODUCT_SEARCH_FIELDS = ('name', 'description')
CATEGORY_SEARCH_FIELDS = ('name', 'slug', 'description', 'parent__name')
COLLECTION_SEARCH_FIELDS = ('name', 'slug')
ATTRIBUTES_SEARCH_FIELDS = ('name', 'slug')


def _filter_attributes_by_product_types(attribute_qs, product_qs):
    product_types = set(product_qs.values_list('product_type_id', flat=True))
    return attribute_qs.filter(
        Q(product_type__in=product_types)
        | Q(product_variant_type__in=product_types))


def resolve_attributes(info, category_id=None, collection_id=None, query=None):
    qs = models.Attribute.objects.all()
    qs = filter_by_query_param(qs, query, ATTRIBUTES_SEARCH_FIELDS)

    if category_id:
        # Filter attributes by product types belonging to the given category.
        category = graphene.Node.get_node_from_global_id(
            info, category_id, Category)
        if category:
            tree = category.get_descendants(include_self=True)
            product_qs = models.Product.objects.filter(category__in=tree)
            qs = _filter_attributes_by_product_types(qs, product_qs)
        else:
            qs = qs.none()

    if collection_id:
        # Filter attributes by product types belonging to the given collection.
        collection = graphene.Node.get_node_from_global_id(
            info, collection_id, Collection)
        if collection:
            product_qs = collection.products.all()
            qs = _filter_attributes_by_product_types(qs, product_qs)
        else:
            qs = qs.none()

    qs = qs.order_by('name')
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)


def resolve_categories(info, query, level=None):
    qs = models.Category.objects.prefetch_related('children')
    if level is not None:
        qs = qs.filter(level=level)
    qs = filter_by_query_param(qs, query, CATEGORY_SEARCH_FIELDS)
    qs = qs.order_by('name')
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)


def resolve_collections(info, query):
    user = info.context.user
    qs = models.Collection.objects.visible_to_user(user)
    qs = filter_by_query_param(qs, query, COLLECTION_SEARCH_FIELDS)
    qs = qs.order_by('name')
    return gql_optimizer.query(qs, info)


def resolve_digital_contents(info):
    qs = models.DigitalContent.objects.all()
    return gql_optimizer.query(qs, info)


def resolve_products(
        info, attributes=None, categories=None, collections=None,
        price_lte=None, price_gte=None, sort_by=None, stock_availability=None,
        query=None, **_kwargs):

    user = info.context.user
    qs = models.Product.objects.visible_to_user(user)

    if query:
        search = picker.pick_backend()
        qs &= search(query)

    if attributes:
        qs = filter_products_by_attributes(qs, attributes)

    if categories:
        categories = get_nodes(categories, Category)
        qs = filter_products_by_categories(qs, categories)

    if collections:
        collections = get_nodes(collections, Collection)
        qs = filter_products_by_collections(qs, collections)
    if stock_availability:
        qs = filter_products_by_stock_availability(qs, stock_availability)

    qs = filter_products_by_price(qs, price_lte, price_gte)
    qs = sort_qs(qs, sort_by)
    qs = qs.distinct()

    return gql_optimizer.query(qs, info)


def resolve_product_types(info):
    qs = models.ProductType.objects.all()
    qs = qs.order_by('name')
    return gql_optimizer.query(qs, info)


def resolve_product_variants(info, ids=None):
    user = info.context.user
    visible_products = models.Product.objects.visible_to_user(
        user).values_list('pk', flat=True)
    qs = models.ProductVariant.objects.filter(
        product__id__in=visible_products)
    if ids:
        db_ids = [
            get_database_id(info, node_id, only_type=ProductVariant)
            for node_id in ids]
        qs = qs.filter(pk__in=db_ids)
    return gql_optimizer.query(qs, info)


def resolve_report_product_sales(period):
    qs = models.ProductVariant.objects.prefetch_related(
        'product', 'product__images', 'order_lines__order').all()

    # exclude draft and canceled orders
    exclude_status = [OrderStatus.DRAFT, OrderStatus.CANCELED]
    qs = qs.exclude(order_lines__order__status__in=exclude_status)

    # filter by period
    qs = filter_by_period(qs, period, 'order_lines__order__created')

    qs = qs.annotate(quantity_ordered=Sum('order_lines__quantity'))
    qs = qs.filter(quantity_ordered__isnull=False)
    return qs.order_by('-quantity_ordered')
