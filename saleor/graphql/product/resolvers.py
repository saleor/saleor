from django.db.models import Q

from ...product import models
from ...product.utils import products_visible_to_user
from ..utils import filter_by_query_param, get_node
from .types import Category

PRODUCT_SEARCH_FIELDS = ('name', 'description', 'category__name')
CATEGORY_SEARCH_FIELDS = ('name', 'slug', 'description', 'parent__name')
COLLECTION_SEARCH_FIELDS = ('name', 'slug')
ATTRIBUTES_SEARCH_FIELDS = ('name', 'slug')


def resolve_attributes(category_id, info, query):
    queryset = models.ProductAttribute.objects.prefetch_related('values')
    queryset = filter_by_query_param(queryset, query, ATTRIBUTES_SEARCH_FIELDS)
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


def resolve_categories(info, query, level=None):
    queryset = models.Category.objects.all()
    if level is not None:
        queryset = queryset.filter(level=level)
    queryset = filter_by_query_param(queryset, query, CATEGORY_SEARCH_FIELDS)
    return queryset.distinct()


def resolve_collections(info, query):
    # FIXME: Return collections based on user after rebasing to master
    queryset = models.Collection.objects.all()
    queryset = filter_by_query_param(queryset, query, COLLECTION_SEARCH_FIELDS)
    return queryset


def resolve_products(info, category_id, query):
    user = info.context.user
    queryset = products_visible_to_user(
        user=user).prefetch_related('Category').distinct()
    queryset = filter_by_query_param(queryset, query, PRODUCT_SEARCH_FIELDS)
    if category_id is not None:
        category = get_node(info, category_id, only_type=Category)
        return queryset.filter(category=category).distinct()
    return queryset


def resolve_product_types():
    return models.ProductType.objects.all().distinct()
