from decimal import Decimal

import pytest

from ....core.postgres import FlatConcatSearchVector
from ....core.prices import Money, TaxedMoney
from ....order.models import Order, OrderLine
from ....order.search import prepare_order_search_vector_value
from ....tax.utils import get_tax_class_kwargs_for_order_line
from ...models import Allocation


@pytest.fixture
def allocation(order_line, stock):
    return Allocation.objects.create(
        order_line=order_line, stock=stock, quantity_allocated=order_line.quantity
    )


@pytest.fixture
def allocations(order_list, stock, channel_USD):
    variant = stock.product_variant
    product = variant.product
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    net = variant.get_price(channel_listing)
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    price = TaxedMoney(net=net, gross=gross)
    lines = OrderLine.objects.bulk_create(
        [
            OrderLine(
                order=order_list[0],
                variant=variant,
                quantity=1,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                product_variant_id=variant.get_global_id(),
                is_shipping_required=variant.is_shipping_required(),
                is_gift_card=variant.is_gift_card(),
                unit_price=price,
                total_price=price,
                tax_rate=Decimal("0.23"),
                **get_tax_class_kwargs_for_order_line(product.product_type.tax_class),
            ),
            OrderLine(
                order=order_list[1],
                variant=variant,
                quantity=2,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                product_variant_id=variant.get_global_id(),
                is_shipping_required=variant.is_shipping_required(),
                is_gift_card=variant.is_gift_card(),
                unit_price=price,
                total_price=price,
                tax_rate=Decimal("0.23"),
                **get_tax_class_kwargs_for_order_line(product.product_type.tax_class),
            ),
            OrderLine(
                order=order_list[2],
                variant=variant,
                quantity=4,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                product_variant_id=variant.get_global_id(),
                is_shipping_required=variant.is_shipping_required(),
                is_gift_card=variant.is_gift_card(),
                unit_price=price,
                total_price=price,
                tax_rate=Decimal("0.23"),
                **get_tax_class_kwargs_for_order_line(product.product_type.tax_class),
            ),
        ]
    )

    for order in order_list:
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
    Order.objects.bulk_update(order_list, ["search_vector"])

    return Allocation.objects.bulk_create(
        [
            Allocation(
                order_line=lines[0], stock=stock, quantity_allocated=lines[0].quantity
            ),
            Allocation(
                order_line=lines[1], stock=stock, quantity_allocated=lines[1].quantity
            ),
            Allocation(
                order_line=lines[2], stock=stock, quantity_allocated=lines[2].quantity
            ),
        ]
    )
