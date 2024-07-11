from typing import Optional

from django.db.models import Exists, OuterRef, Sum

from ...channel.models import Channel
from ...order import OrderStatus
from ...order.models import Order
from ...permission.utils import has_one_of_permissions
from ...product import models
from ...product.models import ALL_PRODUCTS_PERMISSIONS
from ..channel import ChannelQsContext
from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..core.tracing import traced_resolver
from ..core.utils import from_global_id_or_error
from ..utils import get_user_or_app_from_context
from ..utils.filters import filter_by_period


def resolve_categories(info: ResolveInfo, level=None):
    qs = models.Category.objects.using(
        get_database_connection_name(info.context)
    ).prefetch_related("children")
    if level is not None:
        qs = qs.filter(level=level)
    return qs


def resolve_collection_by_id(info: ResolveInfo, id, channel_slug, requestor):
    return (
        models.Collection.objects.using(get_database_connection_name(info.context))
        .visible_to_user(requestor, channel_slug=channel_slug)
        .filter(id=id)
        .first()
    )


def resolve_collection_by_slug(info: ResolveInfo, slug, channel_slug, requestor):
    return (
        models.Collection.objects.using(get_database_connection_name(info.context))
        .visible_to_user(requestor, channel_slug)
        .filter(slug=slug)
        .first()
    )


def resolve_collections(info: ResolveInfo, channel_slug):
    requestor = get_user_or_app_from_context(info.context)
    qs = models.Collection.objects.using(
        get_database_connection_name(info.context)
    ).visible_to_user(requestor, channel_slug)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_digital_content_by_id(info, id):
    return (
        models.DigitalContent.objects.using(get_database_connection_name(info.context))
        .filter(pk=id)
        .first()
    )


def resolve_digital_contents(info: ResolveInfo):
    return models.DigitalContent.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_product(
    info: ResolveInfo,
    id,
    slug,
    external_reference,
    channel: Optional[Channel],
    limited_channel_access: bool,
    requestor,
):
    database_connection_name = get_database_connection_name(info.context)
    qs = models.Product.objects.using(database_connection_name).visible_to_user(
        requestor, channel, limited_channel_access
    )
    if id:
        _type, id = from_global_id_or_error(id, "Product")
        return qs.filter(id=id).first()
    elif slug:
        return qs.filter(slug=slug).first()
    else:
        return qs.filter(external_reference=external_reference).first()


@traced_resolver
def resolve_products(
    info: ResolveInfo,
    requestor,
    channel: Optional[Channel],
    limited_channel_access: bool,
) -> ChannelQsContext:
    connection_name = get_database_connection_name(info.context)
    qs = models.Product.objects.using(connection_name).visible_to_user(
        requestor, channel, limited_channel_access
    )
    if not has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
        if channel:
            product_channel_listings = (
                models.ProductChannelListing.objects.using(connection_name)
                .filter(channel_id=channel.id, visible_in_listings=True)
                .values("id")
            )
            qs = qs.filter(
                Exists(product_channel_listings.filter(product_id=OuterRef("pk")))
            )
        else:
            qs = models.Product.objects.none()
    channel_slug = channel.slug if channel else None
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_product_type_by_id(info, id):
    return (
        models.ProductType.objects.using(get_database_connection_name(info.context))
        .filter(pk=id)
        .first()
    )


def resolve_product_types(info: ResolveInfo):
    return models.ProductType.objects.using(
        get_database_connection_name(info.context)
    ).all()


@traced_resolver
def resolve_variant(
    info: ResolveInfo,
    id,
    sku,
    external_reference,
    *,
    channel: Optional[Channel],
    limited_channel_access: bool,
    requestor,
    requestor_has_access_to_all,
):
    connection_name = get_database_connection_name(info.context)
    visible_products = (
        models.Product.objects.using(connection_name)
        .visible_to_user(requestor, channel, limited_channel_access)
        .values_list("pk", flat=True)
    )
    qs = models.ProductVariant.objects.using(connection_name).filter(
        product__id__in=visible_products
    )
    if not requestor_has_access_to_all:
        qs = qs.available_in_channel(channel)
    if id:
        _, id = from_global_id_or_error(id, "ProductVariant")
        return qs.filter(pk=id).first()
    elif sku:
        return qs.filter(sku=sku).first()
    else:
        return qs.filter(external_reference=external_reference).first()


@traced_resolver
def resolve_product_variants(
    info: ResolveInfo,
    requestor,
    ids=None,
    channel: Optional[Channel] = None,
    limited_channel_access: bool = False,
) -> ChannelQsContext:
    connection_name = get_database_connection_name(info.context)

    qs = models.ProductVariant.objects.using(connection_name).visible_to_user(
        requestor, channel, limited_channel_access
    )

    if ids:
        db_ids = [
            from_global_id_or_error(node_id, "ProductVariant")[1] for node_id in ids
        ]
        qs = qs.filter(pk__in=db_ids)

    channel_slug = channel.slug if channel else None
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_report_product_sales(info, period, channel_slug) -> ChannelQsContext:
    connection_name = get_database_connection_name(info.context)
    qs = models.ProductVariant.objects.using(connection_name).all()

    # filter by period
    qs = filter_by_period(qs, period, "order_lines__order__created_at")

    # annotate quantity
    qs = qs.annotate(quantity_ordered=Sum("order_lines__quantity"))

    # filter by channel and order status
    channels = (
        Channel.objects.using(connection_name).filter(slug=channel_slug).values("pk")
    )
    exclude_status = [OrderStatus.DRAFT, OrderStatus.CANCELED, OrderStatus.EXPIRED]
    orders = (
        Order.objects.using(connection_name)
        .exclude(status__in=exclude_status)
        .filter(Exists(channels.filter(pk=OuterRef("channel_id")).values("pk")))
    )
    qs = qs.filter(
        Exists(orders.filter(pk=OuterRef("order_lines__order_id"))),
        quantity_ordered__isnull=False,
    )

    # order by quantity ordered
    qs = qs.order_by("-quantity_ordered")

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)
