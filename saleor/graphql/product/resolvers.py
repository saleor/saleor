from django.db.models import Q

from ...product import models
from ...product.utils import products_visible_to_user
from ..utils import get_node
from .types import Category, SelectedAttribute


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


def resolve_categories(info, level=None):
    qs = models.Category.objects.all()
    if level is not None:
        qs = qs.filter(level=level)
    return qs.distinct()


def resolve_collections(info):
    return models.Collection.objects.all()


def resolve_products(info, category_id):
    user = info.context.user
    products = products_visible_to_user(user=user).distinct()
    if category_id is not None:
        category = get_node(info, category_id, only_type=Category)
        return products.filter(category=category).distinct()
    return products


def resolve_product_types():
    return models.ProductType.objects.all().distinct()
