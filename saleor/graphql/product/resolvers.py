import graphene
from django.db.models import Sum, Q

from ...order import OrderStatus
from ...product import models
from ...product.utils import products_with_details
from ..utils import filter_by_query_param, filter_by_period, get_database_id
from .types import Category, ProductVariant, StockAvailability

PRODUCT_SEARCH_FIELDS = ('name', 'description', 'category__name')
CATEGORY_SEARCH_FIELDS = ('name', 'slug', 'description', 'parent__name')
COLLECTION_SEARCH_FIELDS = ('name', 'slug')
ATTRIBUTES_SEARCH_FIELDS = ('name', 'slug')


def resolve_attributes(info, category_id, query):
    queryset = models.Attribute.objects.prefetch_related('values')
    queryset = filter_by_query_param(queryset, query, ATTRIBUTES_SEARCH_FIELDS)
    if category_id:
        # Get attributes that are used with product types
        # within the given category.
        category = graphene.Node.get_node_from_global_id(
            info, category_id, Category)
        if category is None:
            return queryset.none()
        tree = category.get_descendants(include_self=True)
        product_types = {
            obj[0]
            for obj in models.Product.objects.filter(
                category__in=tree).values_list('product_type_id')}
        queryset = queryset.filter(
            Q(product_type__in=product_types)
            | Q(product_variant_type__in=product_types))
    return queryset.distinct()


def resolve_categories(info, query, level=None):
    queryset = models.Category.objects.all()
    if level is not None:
        queryset = queryset.filter(level=level)
    queryset = filter_by_query_param(queryset, query, CATEGORY_SEARCH_FIELDS)
    return queryset.distinct()


def resolve_collections(info, query):
    user = info.context.user
    if user.has_perm('product.manage_products'):
        qs = models.Collection.objects.all()
    else:
        qs = models.Collection.objects.public()
    return filter_by_query_param(qs, query, COLLECTION_SEARCH_FIELDS)


def resolve_products(info, category_id, stock_availability, query):
    user = info.context.user
    qs = products_with_details(user=user)
    qs = filter_by_query_param(qs, query, PRODUCT_SEARCH_FIELDS)

    if category_id is not None:
        category = graphene.Node.get_node_from_global_id(
            info, category_id, Category)
        if not category:
            return qs.none()
        qs = qs.filter(category=category)

    if stock_availability:
        qs = qs.annotate(total_quantity=Sum('variants__quantity'))
        if stock_availability == StockAvailability.IN_STOCK:
            qs = qs.filter(total_quantity__gt=0)
        elif stock_availability == StockAvailability.OUT_OF_STOCK:
            qs = qs.filter(total_quantity__lte=0)

    return qs.distinct()


def resolve_product_types():
    return models.ProductType.objects.all().distinct()


def resolve_product_variants(info, ids=None):
    queryset = models.ProductVariant.objects.distinct()
    if ids:
        db_ids = [
            get_database_id(info, node_id, only_type=ProductVariant)
            for node_id in ids]
        queryset = queryset.filter(pk__in=db_ids)
    return queryset


def resolve_report_product_sales(info, period):
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
