from django.db.models import Q

from . import types
from ...product import models
from ...product.utils import products_visible_to_user
from ..utils import get_node


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
            attribute_list.append(
                types.SelectedAttribute(name=name, value=value))
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
        category = get_node(info, category_id, only_type=types.Category)
        return products.filter(category=category).distinct()
    return products


def resolve_attributes(category_id, info):
    queryset = models.ProductAttribute.objects.prefetch_related('values')
    if category_id:
        # Get attributes that are used with product types
        # within the given category.
        category = get_node(info, category_id, only_type=types.Category)
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


def resolve_product_types():
    return models.ProductType.objects.all().distinct()
