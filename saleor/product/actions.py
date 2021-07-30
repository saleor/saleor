import itertools
import typing
from collections import namedtuple

from django.db import transaction
from django.db.models import Sum

from saleor.product.models import ProductVariant
from saleor.warehouse.models import Warehouse

from ..plugins.manager import PluginsManager

product_variant_webhook_container = namedtuple(
    "product_variant_webhook_container",
    ("product_variant", "channel_slugs", "prev_quantity"),
)


def get_product_variant_data_from_warehouses(
    variant: ProductVariant, warehouses: typing.List[Warehouse]
):
    channel_slugs = set(
        itertools.chain.from_iterable(
            [
                warehouse.shipping_zones.values_list("channels__slug", flat=True)
                for warehouse in warehouses
            ]
        )
    )
    prev_quantity = _get_product_variant_total_quantity(variant, channel_slugs)
    return product_variant_webhook_container(
        product_variant=variant,
        channel_slugs=channel_slugs,
        prev_quantity=prev_quantity,
    )


def check_and_trigger_back_in_stock_webhook(
    product_variant_data: product_variant_webhook_container, manager: PluginsManager
):
    if _is_variant_back_to_stock(product_variant_data):
        transaction.on_commit(
            lambda: manager.product_variant_back_in_stock(
                product_variant_data.product_variant
            )
        )


def check_and_trigger_out_of_stock_webhook(
    product_variant_data: product_variant_webhook_container, manager: PluginsManager
):
    total_quantity = _get_product_variant_total_quantity(
        product_variant_data.product_variant, product_variant_data.channel_slugs
    )
    if total_quantity <= 0:
        transaction.on_commit(
            lambda: manager.product_variant_out_of_stock(
                product_variant_data.product_variant
            )
        )


def _is_variant_back_to_stock(product_variant_data: product_variant_webhook_container):
    variant = product_variant_data.product_variant
    slugs = product_variant_data.channel_slugs
    return _get_product_variant_total_quantity(variant, slugs) and (
        product_variant_data.prev_quantity <= 0
    )


def _get_product_variant_total_quantity(
    product_variant: ProductVariant, channel_slugs: typing.Iterable
):
    return sum(
        [
            _get_product_variant_quantity(product_variant, channel_slug)
            for channel_slug in channel_slugs
        ]
    )


def _get_product_variant_quantity(product_variant: ProductVariant, channel_slug: str):
    return (
        product_variant.stocks.for_channel(channel_slug).aggregate(  # type: ignore
            Sum("quantity")
        )["quantity__sum"]
        or 0
    )
