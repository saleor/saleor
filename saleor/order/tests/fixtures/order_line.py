from decimal import Decimal

import pytest
from prices import Money, TaxedMoney

from ....warehouse.models import Allocation, Stock
from ... import OrderOrigin
from ...fetch import OrderLineInfo
from ...models import Order


@pytest.fixture
def order_line(order, variant):
    product = variant.product
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    return order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
        tax_class=variant.product.tax_class,
    )


@pytest.fixture
def order_line_on_promotion(order_line, catalogue_promotion):
    variant = order_line.variant

    channel = order_line.order.channel
    reward_value = Decimal("1.0")
    rule = catalogue_promotion.rules.first()
    variant_channel_listing = variant.channel_listings.get(channel=channel)

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    order_line.total_price_gross_amount = (
        variant_channel_listing.discounted_price_amount * order_line.quantity
    )
    order_line.total_price_net_amount = (
        variant_channel_listing.discounted_price_amount * order_line.quantity
    )
    order_line.undiscounted_total_price_gross_amount = (
        variant_channel_listing.price_amount * order_line.quantity
    )
    order_line.undiscounted_total_price_net_amount = (
        variant_channel_listing.price_amount * order_line.quantity
    )

    order_line.unit_price_gross_amount = variant_channel_listing.discounted_price_amount
    order_line.unit_price_net_amount = variant_channel_listing.discounted_price_amount
    order_line.undiscounted_unit_price_gross_amount = (
        variant_channel_listing.price_amount
    )
    order_line.undiscounted_unit_price_net_amount = variant_channel_listing.price_amount

    order_line.base_unit_price_amount = variant_channel_listing.discounted_price_amount
    order_line.undiscounted_base_unit_price_amount = (
        variant_channel_listing.price_amount
    )

    order_line.unit_discount_amount = reward_value
    order_line.save()
    return order_line


@pytest.fixture
def order_line_JPY(order_generator, channel_JPY, product_in_channel_JPY):
    order_JPY = order_generator(
        channel=channel_JPY,
        currency=channel_JPY.currency_code,
    )
    product = product_in_channel_JPY
    variant = product_in_channel_JPY.variants.get()
    channel = order_JPY.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    base_price = variant.get_price(channel_listing)
    currency = base_price.currency
    gross = Money(amount=base_price.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=base_price, gross=gross)
    return order_JPY.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=base_price,
        undiscounted_base_unit_price=base_price,
        tax_rate=Decimal("0.23"),
    )


@pytest.fixture
def order_line_with_allocation_in_many_stocks(
    customer_user, variant_with_many_stocks, channel_USD
):
    address = customer_user.default_billing_address.get_copy()
    variant = variant_with_many_stocks
    stocks = variant.stocks.all().order_by("pk")

    order = Order.objects.create(
        billing_address=address,
        user_email=customer_user.email,
        user=customer_user,
        channel=channel_USD,
        origin=OrderOrigin.CHECKOUT,
        undiscounted_base_shipping_price_amount=Decimal("0.0"),
    )

    product = variant.product
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    order_line = order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
    )

    Allocation.objects.bulk_create(
        [
            Allocation(order_line=order_line, stock=stocks[0], quantity_allocated=2),
            Allocation(order_line=order_line, stock=stocks[1], quantity_allocated=1),
        ]
    )

    stocks_to_update = list(stocks)
    stocks_to_update[0].quantity_allocated = 2
    stocks_to_update[1].quantity_allocated = 1

    Stock.objects.bulk_update(stocks_to_update, ["quantity_allocated"])

    return order_line


@pytest.fixture
def order_line_with_one_allocation(
    customer_user, variant_with_many_stocks, channel_USD
):
    address = customer_user.default_billing_address.get_copy()
    variant = variant_with_many_stocks
    stocks = variant.stocks.all().order_by("pk")

    order = Order.objects.create(
        billing_address=address,
        user_email=customer_user.email,
        user=customer_user,
        channel=channel_USD,
        origin=OrderOrigin.CHECKOUT,
    )

    product = variant.product
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 2
    unit_price = TaxedMoney(net=net, gross=gross)
    order_line = order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
    )

    Allocation.objects.create(
        order_line=order_line, stock=stocks[0], quantity_allocated=1
    )
    stock = stocks[0]
    stock.quantity_allocated = 1
    stock.save(update_fields=["quantity_allocated"])

    return order_line


@pytest.fixture
def lines_info(order_with_lines):
    return [
        OrderLineInfo(
            line=line,
            quantity=line.quantity,
            variant=line.variant,
            warehouse_pk=line.allocations.first().stock.warehouse.pk,
        )
        for line in order_with_lines.lines.all()
    ]


@pytest.fixture
def gift_card_non_shippable_order_line(
    order, gift_card_non_shippable_variant, warehouse
):
    variant = gift_card_non_shippable_variant
    product = variant.product
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 1
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
    )
    Allocation.objects.create(
        order_line=line, stock=variant.stocks.first(), quantity_allocated=line.quantity
    )
    return line


@pytest.fixture
def gift_card_shippable_order_line(order, gift_card_shippable_variant, warehouse):
    variant = gift_card_shippable_variant
    product = variant.product
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
    )
    Allocation.objects.create(
        order_line=line, stock=variant.stocks.first(), quantity_allocated=line.quantity
    )
    return line
