import graphene
from django.db.models import Q

from ...product import models
from ...product.utils import products_with_details
from ..utils import filter_by_query_param, get_database_id
from .types import Category, ProductVariant

PRODUCT_SEARCH_FIELDS = ('name', 'description', 'category__name')
CATEGORY_SEARCH_FIELDS = ('name', 'slug', 'description', 'parent__name')
COLLECTION_SEARCH_FIELDS = ('name', 'slug')
ATTRIBUTES_SEARCH_FIELDS = ('name', 'slug')


def resolve_attributes(info, category_id, query):
    queryset = models.ProductAttribute.objects.prefetch_related('values')
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
    user = info.context.user
    if user.has_perm('product.manage_products'):
        qs = models.Collection.objects.all()
    else:
        qs = models.Collection.objects.public()
    return filter_by_query_param(qs, query, COLLECTION_SEARCH_FIELDS)


def resolve_products(info, category_id, query):
    user = info.context.user
    queryset = products_with_details(user=user).distinct()
    queryset = filter_by_query_param(queryset, query, PRODUCT_SEARCH_FIELDS)
    if category_id is not None:
        category = graphene.Node.get_node_from_global_id(
            info, category_id, Category)
        if not category:
            return queryset.none()
        return queryset.filter(category=category).distinct()
    return queryset


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
