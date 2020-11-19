from typing import Union

from django.db.models import Sum
from promise import Promise

from ...checkout.models import CheckoutLine
from ...order import OrderStatus
from ...order.models import OrderLine
from ...product import models
from ..channel import ChannelContext, ChannelQsContext
from ..channel.dataloaders import (
    ChannelByCheckoutLineIDLoader,
    ChannelByOrderLineIdLoader,
)
from ..product.dataloaders import (
    ProductChannelListingByProductIdAndChannelSlugLoader,
    ProductVariantByIdLoader,
)
from ..utils import get_database_id, get_user_or_app_from_context
from ..utils.filters import filter_by_period
from .filters import filter_products_by_stock_availability


def resolve_category_by_slug(slug):
    return models.Category.objects.filter(slug=slug).first()


def resolve_categories(info, level=None, **_kwargs):
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
    user = info.context.user
    qs = models.Collection.objects.visible_to_user(user, channel_slug)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_digital_contents(_info):
    return models.DigitalContent.objects.all()


def resolve_product_by_id(info, id, channel_slug, requestor):
    return (
        models.Product.objects.visible_to_user(requestor, channel_slug=channel_slug)
        .filter(id=id)
        .first()
    )


def resolve_product_by_slug(info, product_slug, channel_slug, requestor):
    return (
        models.Product.objects.visible_to_user(requestor, channel_slug=channel_slug)
        .filter(slug=product_slug)
        .first()
    )


def resolve_products(
    info, requestor, stock_availability=None, channel_slug=None, **_kwargs
) -> ChannelQsContext:
    qs = models.Product.objects.visible_to_user(requestor, channel_slug)
    if stock_availability:
        qs = filter_products_by_stock_availability(qs, stock_availability)
    if not qs.user_has_access_to_all(requestor):
        qs = qs.annotate_visible_in_listings(channel_slug).exclude(
            visible_in_listings=False
        )
    return ChannelQsContext(qs=qs.distinct(), channel_slug=channel_slug)


def resolve_variant_by_id(info, id, channel_slug, requestor):
    visible_products = models.Product.objects.visible_to_user(
        requestor, channel_slug
    ).values_list("pk", flat=True)
    qs = models.ProductVariant.objects.filter(product__id__in=visible_products)
    return qs.filter(pk=id).first()


def resolve_product_types(info, **_kwargs):
    return models.ProductType.objects.all()


def resolve_product_variant_by_sku(
    info, sku, channel_slug, requestor, requestor_has_access_to_all
):
    visible_products = models.Product.objects.visible_to_user(requestor, channel_slug)
    if not requestor_has_access_to_all:
        visible_products = visible_products.annotate_visible_in_listings(
            channel_slug
        ).exclude(visible_in_listings=False)

    return (
        models.ProductVariant.objects.filter(product__id__in=visible_products)
        .filter(sku=sku)
        .first()
    )


def resolve_product_variants(
    info, requestor_has_access_to_all, requestor, ids=None, channel_slug=None
) -> ChannelQsContext:
    visible_products = models.Product.objects.visible_to_user(requestor, channel_slug)
    if not requestor_has_access_to_all:
        visible_products = visible_products.annotate_visible_in_listings(
            channel_slug
        ).exclude(visible_in_listings=False)

    qs = models.ProductVariant.objects.filter(product__id__in=visible_products)
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


def resolve_variant(
    info,
    root: Union[CheckoutLine, OrderLine],
    channel_dataloader: Union[
        ChannelByCheckoutLineIDLoader, ChannelByOrderLineIdLoader
    ],
):
    context = info.context
    if not root.variant_id:
        return None

    def requestor_has_access_to_variant(data):
        variant, channel = data

        def product_is_available(product_channel_listing):
            if not product_channel_listing:
                return None
            requester = get_user_or_app_from_context(context)
            visible_in_listings = product_channel_listing.visible_in_listings
            requestor_has_access_to_all = models.Product.objects.user_has_access_to_all(
                requester
            )
            if visible_in_listings or requestor_has_access_to_all:
                return ChannelContext(node=variant, channel_slug=channel.slug)
            return None

        return (
            ProductChannelListingByProductIdAndChannelSlugLoader(context)
            .load((variant.product_id, channel.slug))
            .then(product_is_available)
        )

    variant = ProductVariantByIdLoader(context).load(root.variant_id)
    channel = channel_dataloader.load(root.id)

    return Promise.all([variant, channel]).then(requestor_has_access_to_variant)
