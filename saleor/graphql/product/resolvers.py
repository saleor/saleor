from django.db.models import Sum

from ...order import OrderStatus
from ...product import models
from ..channel import ChannelQsContext
from ..utils import get_database_id, get_user_or_app_from_context
from ..utils.filters import filter_by_period
from .filters import filter_products_by_stock_availability


def _return_visible_product(requestor, channel_slug, requestor_has_access_to_all):
    visible_products = models.Product.objects.visible_to_user(requestor, channel_slug)
    if not requestor_has_access_to_all:
        visible_products = visible_products.annotate_visible_in_listings(
            channel_slug
        ).exclude(visible_in_listings=False)
    return visible_products


def resolve_category_by_slug(slug):
    return models.Category.objects.filter(slug=slug).first()


def resolve_categories(_info, level=None, **_kwargs):
    qs = models.Category.objects.prefetch_related("children")
    if level is not None:
        qs = qs.filter(level=level)
    return qs.distinct()


def resolve_collection_by_id(info, id, channel_slug, requestor):
    return (
        models.Collection.objects.visible_to_user(requestor, channel_slug=channel_slug)
        .filter(id=id)
        .first()
    )


def resolve_collection_by_slug(info, slug, channel_slug, requestor):
    return (
        models.Collection.objects.visible_to_user(requestor, channel_slug)
        .filter(slug=slug)
        .first()
    )


def resolve_collections(info, channel_slug):
    requestor = get_user_or_app_from_context(info.context)
    qs = models.Collection.objects.visible_to_user(requestor, channel_slug)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_digital_contents(_info):
    return models.DigitalContent.objects.all()


def resolve_product_by_id(
    info, id, channel_slug, requestor, requestor_has_access_to_all
):
    visible_products = _return_visible_product(
        requestor, channel_slug, requestor_has_access_to_all
    )

    return visible_products.filter(id=id).first()


def resolve_product_by_slug(
    info, product_slug, channel_slug, requestor, requestor_has_access_to_all
):
    visible_products = _return_visible_product(
        requestor, channel_slug, requestor_has_access_to_all
    )

    return visible_products.filter(slug=product_slug).first()


def resolve_products(
    info,
    requestor,
    requestor_has_access_to_all,
    stock_availability=None,
    channel_slug=None,
    **_kwargs
) -> ChannelQsContext:
    qs = _return_visible_product(requestor, channel_slug, requestor_has_access_to_all)
    if stock_availability:
        qs = filter_products_by_stock_availability(qs, stock_availability)
    return ChannelQsContext(qs=qs.distinct(), channel_slug=channel_slug)


def resolve_variant_by_id(
    info, id, channel_slug, requestor, requestor_has_access_to_all
):
    visible_products = _return_visible_product(
        requestor, channel_slug, requestor_has_access_to_all
    )
    qs = models.ProductVariant.objects.filter(product__in=visible_products)
    if not requestor_has_access_to_all:
        qs = qs.available_in_channel(channel_slug)

    return qs.filter(pk=id).first()


def resolve_product_types(_info, **_kwargs):
    return models.ProductType.objects.all()


def resolve_product_variant_by_sku(
    info, sku, channel_slug, requestor, requestor_has_access_to_all
):
    visible_products = _return_visible_product(
        requestor, channel_slug, requestor_has_access_to_all
    )
    qs = models.ProductVariant.objects.filter(product__in=visible_products)
    if not requestor_has_access_to_all:
        qs = qs.available_in_channel(channel_slug)
    return qs.filter(sku=sku).first()


def resolve_product_variants(
    info, requestor_has_access_to_all, requestor, ids=None, channel_slug=None
) -> ChannelQsContext:
    visible_products = _return_visible_product(
        requestor, channel_slug, requestor_has_access_to_all
    )

    qs = models.ProductVariant.objects.filter(product__in=visible_products)
    if not requestor_has_access_to_all:
        qs = qs.available_in_channel(channel_slug=channel_slug)
    if ids:
        db_ids = [get_database_id(info, node_id, "ProductVariant") for node_id in ids]
        qs = qs.filter(pk__in=db_ids)
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_report_product_sales(period, channel_slug) -> ChannelQsContext:
    qs = models.ProductVariant.objects.all()

    # exclude draft and canceled orders
    exclude_status = [OrderStatus.DRAFT, OrderStatus.CANCELED]
    qs = qs.exclude(order_lines__order__status__in=exclude_status)

    # filter by period
    qs = filter_by_period(qs, period, "order_lines__order__created")

    qs = qs.annotate(quantity_ordered=Sum("order_lines__quantity"))
    qs = qs.filter(
        quantity_ordered__isnull=False, order_lines__order__channel__slug=channel_slug
    )
    qs = qs.order_by("-quantity_ordered")
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)
