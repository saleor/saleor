import graphene_django_optimizer as gql_optimizer
from django.db.models import Sum

from ...order import OrderStatus
from ...product import models
from ..utils import filter_by_period, get_database_id, get_user_or_app_from_context
from .filters import (
    filter_attributes_by_product_types,
    filter_products_by_stock_availability,
)


def resolve_attributes(info, qs=None, in_category=None, in_collection=None, **_kwargs):
    qs = qs or models.Attribute.objects.get_visible_to_user(info.context.user)

    if in_category:
        qs = filter_attributes_by_product_types(qs, "in_category", in_category)

    if in_collection:
        qs = filter_attributes_by_product_types(qs, "in_collection", in_collection)

    qs = qs.distinct()
    return gql_optimizer.query(qs, info)


def resolve_categories(info, level=None, **_kwargs):
    qs = models.Category.objects.prefetch_related("children")
    if level is not None:
        qs = qs.filter(level=level)
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)


def resolve_collections(info, **_kwargs):
    user = info.context.user
    qs = models.Collection.objects.visible_to_user(user)
    return gql_optimizer.query(qs, info)


def resolve_digital_contents(info):
    qs = models.DigitalContent.objects.all()
    return gql_optimizer.query(qs, info)


def resolve_products(info, stock_availability=None, **_kwargs):

    user = get_user_or_app_from_context(info.context)
    qs = models.Product.objects.visible_to_user(user)

    if stock_availability:
        qs = filter_products_by_stock_availability(qs, stock_availability)

    qs = qs.distinct()

    return gql_optimizer.query(qs, info)


def resolve_product_types(info, **_kwargs):
    qs = models.ProductType.objects.all()
    return gql_optimizer.query(qs, info)


def resolve_product_variants(info, ids=None):
    user = info.context.user
    visible_products = models.Product.objects.visible_to_user(user).values_list(
        "pk", flat=True
    )
    qs = models.ProductVariant.objects.filter(product__id__in=visible_products)
    if ids:
        db_ids = [get_database_id(info, node_id, "ProductVariant") for node_id in ids]
        qs = qs.filter(pk__in=db_ids)
    return gql_optimizer.query(qs, info)


def resolve_report_product_sales(period):
    qs = models.ProductVariant.objects.prefetch_related(
        "product", "product__images", "order_lines__order"
    ).all()

    # exclude draft and canceled orders
    exclude_status = [OrderStatus.DRAFT, OrderStatus.CANCELED]
    qs = qs.exclude(order_lines__order__status__in=exclude_status)

    # filter by period
    qs = filter_by_period(qs, period, "order_lines__order__created")

    qs = qs.annotate(quantity_ordered=Sum("order_lines__quantity"))
    qs = qs.filter(quantity_ordered__isnull=False)
    return qs.order_by("-quantity_ordered")
