from typing import TYPE_CHECKING, Optional

import graphene_django_optimizer as gql_optimizer
from django.db.models import Sum
from graphql import GraphQLError
from graphql_relay import from_global_id

from ...order import OrderStatus
from ...product import models
from ...search.backends import picker
from ..utils import filter_by_period, filter_by_query_param, get_database_id, get_nodes
from .enums import AttributeSortField, OrderDirection
from .filters import (
    filter_attributes_by_product_types,
    filter_products_by_attributes,
    filter_products_by_categories,
    filter_products_by_collections,
    filter_products_by_minimal_price,
    filter_products_by_price,
    filter_products_by_stock_availability,
    sort_qs,
)

if TYPE_CHECKING:
    from ..product.types import ProductOrder  # noqa

PRODUCT_SEARCH_FIELDS = ("name", "description")
PRODUCT_TYPE_SEARCH_FIELDS = ("name",)
CATEGORY_SEARCH_FIELDS = ("name", "slug", "description", "parent__name")
COLLECTION_SEARCH_FIELDS = ("name", "slug")
ATTRIBUTES_SEARCH_FIELDS = ("name", "slug")


def resolve_attributes(
    info,
    qs=None,
    in_category=None,
    in_collection=None,
    query=None,
    sort_by=None,
    **_kwargs,
):
    qs = qs or models.Attribute.objects.get_visible_to_user(info.context.user)
    qs = filter_by_query_param(qs, query, ATTRIBUTES_SEARCH_FIELDS)

    if in_category:
        qs = filter_attributes_by_product_types(qs, "in_category", in_category)

    if in_collection:
        qs = filter_attributes_by_product_types(qs, "in_collection", in_collection)

    if sort_by:
        is_asc = sort_by["direction"] == OrderDirection.ASC.value
        if sort_by["field"] == AttributeSortField.DASHBOARD_VARIANT_POSITION.value:
            qs = qs.variant_attributes_sorted(is_asc)
        elif sort_by["field"] == AttributeSortField.DASHBOARD_PRODUCT_POSITION.value:
            qs = qs.product_attributes_sorted(is_asc)
        else:
            qs = sort_qs(qs, sort_by)
    else:
        qs = qs.order_by("name")

    qs = qs.distinct()
    return gql_optimizer.query(qs, info)


def resolve_categories(info, query, level=None):
    qs = models.Category.objects.prefetch_related("children")
    if level is not None:
        qs = qs.filter(level=level)
    qs = filter_by_query_param(qs, query, CATEGORY_SEARCH_FIELDS)
    qs = qs.order_by("name")
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)


def resolve_collections(info, query):
    user = info.context.user
    qs = models.Collection.objects.visible_to_user(user)
    qs = filter_by_query_param(qs, query, COLLECTION_SEARCH_FIELDS)
    qs = qs.order_by("name")
    return gql_optimizer.query(qs, info)


def resolve_digital_contents(info):
    qs = models.DigitalContent.objects.all()
    return gql_optimizer.query(qs, info)


def sort_products(qs: models.ProductsQueryset, sort_by: Optional["ProductOrder"]):
    if sort_by is None:
        return qs

    # Check if one of the required fields was provided
    if sort_by.field and sort_by.attribute_id:
        raise GraphQLError(
            "You must provide either `field` or `attributeId` to sort the products."
        )

    if not sort_by.field and not sort_by.attribute_id:
        return qs

    direction = sort_by.direction
    sorting_field = sort_by.field

    # If an attribute ID was passed, attempt to convert it
    if sort_by.attribute_id:
        graphene_type, attribute_pk = from_global_id(sort_by.attribute_id)
        is_ascending = direction == OrderDirection.ASC

        # If the passed attribute ID is valid, execute the sorting
        if attribute_pk.isnumeric() and graphene_type == "Attribute":
            qs = qs.sort_by_attribute(attribute_pk, ascending=is_ascending)
    elif sorting_field:
        qs = qs.order_by(f"{direction}{sorting_field}")

    return qs


def resolve_products(
    info,
    attributes=None,
    categories=None,
    collections=None,
    price_lte=None,
    price_gte=None,
    minimal_price_lte=None,
    minimal_price_gte=None,
    sort_by=None,
    stock_availability=None,
    query=None,
    **_kwargs,
):

    user = info.context.user
    qs = models.Product.objects.visible_to_user(user)
    qs = sort_products(qs, sort_by)

    if query:
        search = picker.pick_backend()
        qs &= search(query)

    if attributes:
        qs = filter_products_by_attributes(qs, attributes)

    if categories:
        categories = get_nodes(categories, "Category", models.Category)
        qs = filter_products_by_categories(qs, categories)

    if collections:
        collections = get_nodes(collections, "Collection", models.Collection)
        qs = filter_products_by_collections(qs, collections)

    if stock_availability:
        qs = filter_products_by_stock_availability(qs, stock_availability)

    qs = filter_products_by_price(qs, price_lte, price_gte)
    qs = filter_products_by_minimal_price(qs, minimal_price_lte, minimal_price_gte)
    qs = qs.distinct()

    return gql_optimizer.query(qs, info)


def resolve_product_types(info, query):
    qs = models.ProductType.objects.all()
    qs = filter_by_query_param(qs, query, PRODUCT_TYPE_SEARCH_FIELDS)
    qs = qs.order_by("name")
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
