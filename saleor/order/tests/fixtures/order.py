import datetime
from datetime import timedelta
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time
from prices import Money, TaxedMoney

from ....checkout.utils import get_prices_of_discounted_specific_product
from ....core import JobStatus
from ....core.taxes import zero_money
from ....discount import DiscountType, RewardType, RewardValueType, VoucherType
from ....discount.models import NotApplicable, Voucher
from ....discount.utils.voucher import (
    get_products_voucher_discount,
    validate_voucher_in_order,
)
from ....payment.model_helpers import get_subtotal
from ....plugins.manager import get_plugins_manager
from ....product.models import (
    Product,
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)
from ....tax.utils import calculate_tax_rate, get_tax_class_kwargs_for_order_line
from ....warehouse.models import Allocation, PreorderAllocation, Stock
from ... import OrderOrigin, OrderStatus
from ...actions import cancel_fulfillment, fulfill_order_lines
from ...events import (
    OrderEvents,
    fulfillment_refunded_event,
    order_added_products_event,
)
from ...fetch import OrderLineInfo
from ...models import FulfillmentStatus, Order, OrderEvent, OrderLine
from ...search import prepare_order_search_vector_value
from ...utils import get_voucher_discount_assigned_to_order


def recalculate_order(order):
    lines = OrderLine.objects.filter(order_id=order.pk)
    prices = [line.total_price for line in lines]
    total = sum(prices, order.shipping_price)
    undiscounted_total = TaxedMoney(total.net, total.gross)

    try:
        discount = get_voucher_discount_for_order(order)
    except NotApplicable:
        discount = zero_money(order.currency)

    discount = min(discount, total.gross)
    total -= discount

    order.total = total
    order.subtotal = get_subtotal(order.lines.all(), order.currency)
    order.undiscounted_total = undiscounted_total

    if discount:
        assigned_order_discount = get_voucher_discount_assigned_to_order(order)
        if assigned_order_discount:
            assigned_order_discount.amount_value = discount.amount
            assigned_order_discount.value = discount.amount
            assigned_order_discount.save(update_fields=["value", "amount_value"])

    order.save()


def get_voucher_discount_for_order(order: Order) -> Money:
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    if not order.voucher:
        return zero_money(order.currency)
    validate_voucher_in_order(order)
    subtotal = order.subtotal
    if order.voucher.type == VoucherType.ENTIRE_ORDER:
        return order.voucher.get_discount_amount_for(subtotal.gross, order.channel)
    if order.voucher.type == VoucherType.SHIPPING:
        return order.voucher.get_discount_amount_for(
            order.shipping_price.gross, order.channel
        )
    if order.voucher.type == VoucherType.SPECIFIC_PRODUCT:
        return get_products_voucher_discount_for_order(order, order.voucher)
    raise NotImplementedError("Unknown discount type")


def get_products_voucher_discount_for_order(order: Order, voucher: Voucher) -> Money:
    """Calculate products discount value for a voucher, depending on its type."""
    prices = None
    if voucher and voucher.type == VoucherType.SPECIFIC_PRODUCT:
        prices = get_prices_of_discounted_specific_product(order.lines.all(), voucher)
    if not prices:
        msg = "This offer is only valid for selected items."
        raise NotApplicable(msg)
    return get_products_voucher_discount(voucher, prices, order.channel)


@pytest.fixture
def orders(customer_user, channel_USD, channel_PLN):
    return Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                status=OrderStatus.CANCELED,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.UNFULFILLED,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.PARTIALLY_FULFILLED,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                channel=channel_PLN,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.DRAFT,
                channel=channel_PLN,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.UNCONFIRMED,
                channel=channel_PLN,
            ),
        ]
    )


@pytest.fixture
def orders_from_checkout(customer_user, checkout):
    return Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                status=OrderStatus.CANCELED,
                channel=checkout.channel,
                checkout_token=checkout.token,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.UNFULFILLED,
                channel=checkout.channel,
                checkout_token=checkout.token,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                channel=checkout.channel,
                checkout_token=checkout.token,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                channel=checkout.channel,
                checkout_token=checkout.token,
            ),
        ]
    )


@pytest.fixture
def order_generator(customer_user, channel_USD):
    address = customer_user.default_billing_address.get_copy()

    def create_order(
        billing_address=address,
        channel=channel_USD,
        currency=channel_USD.currency_code,
        shipping_address=address,
        user_email=customer_user.email,
        user=customer_user,
        origin=OrderOrigin.CHECKOUT,
        should_refresh_prices=False,
        checkout_token="",
        status=OrderStatus.UNFULFILLED,
        search_vector_class=None,
    ):
        order = Order.objects.create(
            billing_address=billing_address,
            channel=channel,
            currency=currency,
            shipping_address=shipping_address,
            user_email=user_email,
            user=user,
            origin=origin,
            should_refresh_prices=should_refresh_prices,
            metadata={"key": "value"},
            private_metadata={"secret_key": "secret_value"},
            checkout_token=checkout_token,
            status=status,
            undiscounted_base_shipping_price_amount=Decimal("0.0"),
        )
        if search_vector_class:
            search_vector = search_vector_class(
                *prepare_order_search_vector_value(order)
            )
            order.search_vector = search_vector
            order.save(update_fields=["search_vector"])
        return order

    return create_order


@pytest.fixture
def order(order_generator):
    return order_generator()


@pytest.fixture
def order_unconfirmed(order):
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    return order


@pytest.fixture
def order_list(customer_user, channel_USD):
    address = customer_user.default_billing_address.get_copy()
    data = {
        "billing_address": address,
        "user": customer_user,
        "user_email": customer_user.email,
        "channel": channel_USD,
        "origin": OrderOrigin.CHECKOUT,
    }
    order = Order.objects.create(**data)
    order1 = Order.objects.create(**data)
    order2 = Order.objects.create(**data)

    return [order, order1, order2]


@pytest.fixture
def order_list_with_cc_orders(orders, warehouse_for_cc):
    order_1 = orders[0]
    order_1.collection_point = warehouse_for_cc
    order_1.collection_point_name = warehouse_for_cc.name

    order_2 = orders[1]
    order_2.collection_point_name = warehouse_for_cc.name

    order_3 = orders[2]
    order_3.collection_point = warehouse_for_cc

    cc_orders = [order_1, order_2, order_3]

    Order.objects.bulk_update(cc_orders, ["collection_point", "collection_point_name"])
    return orders


@pytest.fixture
def order_with_lines(
    order,
    product_type,
    category,
    shipping_zone,
    warehouse,
    channel_USD,
    default_tax_class,
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-8",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime.now(tz=datetime.UTC),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_AA")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    base_price = variant.get_price(channel_listing)
    currency = base_price.currency
    gross = Money(amount=base_price.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=base_price, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
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
        base_unit_price=base_price,
        undiscounted_base_unit_price=base_price,
        tax_rate=Decimal("0.23"),
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    product = Product.objects.create(
        name="Test product 2",
        slug="test-product-9",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=timezone.now(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_B")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(20),
        discounted_price_amount=Decimal(20),
        cost_price_amount=Decimal(2),
        currency=channel_USD.currency_code,
    )
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=2
    )
    stock.refresh_from_db()

    base_price = variant.get_price(channel_listing)
    currency = base_price.currency
    gross = Money(amount=base_price.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=base_price, gross=gross)
    quantity = 2
    line = order.lines.create(
        product_name=str(variant.product),
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
        base_unit_price=base_price,
        undiscounted_base_unit_price=base_price,
        tax_rate=Decimal("0.23"),
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    order.shipping_address = order.billing_address.get_copy()
    order.channel = channel_USD
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_price = shipping_method.channel_listings.get(channel_id=channel_USD.id)
    order.shipping_method_name = shipping_method.name
    order.shipping_method = shipping_method
    order.shipping_tax_class = shipping_method.tax_class
    order.shipping_tax_class_name = shipping_method.tax_class.name
    order.shipping_tax_class_metadata = shipping_method.tax_class.metadata
    order.shipping_tax_class_private_metadata = (
        shipping_method.tax_class.private_metadata
    )  # noqa: E501

    net = shipping_price.get_total()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order.shipping_price = TaxedMoney(net=net, gross=gross)
    order.base_shipping_price = net
    order.undiscounted_base_shipping_price = net
    order.shipping_tax_rate = calculate_tax_rate(order.shipping_price)
    order.save()

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_with_lines_for_cc(
    warehouse_for_cc,
    channel_USD,
    customer_user,
    product_variant_list,
):
    address = customer_user.default_billing_address.get_copy()

    order = Order.objects.create(
        billing_address=address,
        channel=channel_USD,
        currency=channel_USD.currency_code,
        shipping_address=address,
        user_email=customer_user.email,
        user=customer_user,
        origin=OrderOrigin.CHECKOUT,
    )

    order.collection_point = warehouse_for_cc
    order.collection_point_name = warehouse_for_cc.name
    order.save()

    variant = product_variant_list[0]
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    quantity = 1
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
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
        **get_tax_class_kwargs_for_order_line(variant.product.product_type.tax_class),
    )
    Allocation.objects.create(
        order_line=line,
        stock=warehouse_for_cc.stock_set.filter(product_variant=variant).first(),
        quantity_allocated=line.quantity,
    )

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_with_lines_and_catalogue_promotion(
    order_with_lines, channel_USD, catalogue_promotion_without_rules
):
    order = order_with_lines
    promotion = catalogue_promotion_without_rules
    line = order.lines.get(quantity=3)
    variant = line.variant
    reward_value = Decimal(3)
    rule = promotion.rules.create(
        name="Catalogue rule fixed",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel_USD)

    listing = variant.channel_listings.get(channel=channel_USD)
    listing.discounted_price_amount = listing.price_amount - reward_value
    listing.save(update_fields=["discounted_price_amount"])
    listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=order.currency,
    )

    line.discounts.create(
        type=DiscountType.PROMOTION,
        value_type=RewardValueType.FIXED,
        value=reward_value,
        amount_value=reward_value * line.quantity,
        currency=order.currency,
        promotion_rule=rule,
    )
    return order


@pytest.fixture
def order_with_lines_and_order_promotion(
    order_with_lines,
    channel_USD,
    order_promotion_without_rules,
):
    order = order_with_lines
    promotion = order_promotion_without_rules
    rule = promotion.rules.create(
        name="Fixed subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(25),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(channel_USD)

    order.discounts.create(
        promotion_rule=rule,
        type=DiscountType.ORDER_PROMOTION,
        value_type=rule.reward_value_type,
        value=rule.reward_value,
        amount_value=rule.reward_value,
        currency=order.currency,
    )
    return order


@pytest.fixture
def order_with_lines_and_gift_promotion(
    order_with_lines,
    channel_USD,
    order_promotion_without_rules,
    variant_with_many_stocks,
):
    order = order_with_lines
    variant = variant_with_many_stocks
    variant_listing = variant.channel_listings.get(channel=channel_USD)
    promotion = order_promotion_without_rules
    rule = promotion.rules.create(
        name="Gift subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
        },
        reward_type=RewardType.GIFT,
    )
    rule.channels.add(channel_USD)
    rule.gifts.set([variant])

    gift_line = order.lines.create(
        quantity=1,
        variant=variant,
        is_gift=True,
        currency=order.currency,
        unit_price_net_amount=0,
        unit_price_gross_amount=0,
        total_price_net_amount=0,
        total_price_gross_amount=0,
        is_shipping_required=True,
        is_gift_card=False,
    )
    gift_line.discounts.create(
        promotion_rule=rule,
        type=DiscountType.ORDER_PROMOTION,
        value_type=RewardValueType.FIXED,
        value=variant_listing.price_amount,
        amount_value=variant_listing.price_amount,
        currency=order.currency,
    )
    return order


@pytest.fixture
def order_with_lines_and_events(order_with_lines, staff_user):
    events = []
    for event_type, _ in OrderEvents.CHOICES:
        events.append(
            OrderEvent(
                type=event_type,
                order=order_with_lines,
                user=staff_user,
            )
        )
    OrderEvent.objects.bulk_create(events)
    fulfillment_refunded_event(
        order=order_with_lines,
        user=staff_user,
        app=None,
        refunded_lines=[(1, order_with_lines.lines.first())],
        amount=Decimal("10.0"),
        shipping_costs_included=False,
    )
    order_added_products_event(
        order=order_with_lines,
        user=staff_user,
        app=None,
        order_lines=[order_with_lines.lines.first()],
        quantity_diff=1,
    )
    return order_with_lines


@pytest.fixture
def order_with_lines_channel_PLN(
    customer_user,
    product_type,
    category,
    shipping_method_channel_PLN,
    warehouse,
    channel_PLN,
):
    address = customer_user.default_billing_address.get_copy()
    order = Order.objects.create(
        billing_address=address,
        channel=channel_PLN,
        shipping_address=address,
        user_email=customer_user.email,
        user=customer_user,
        origin=OrderOrigin.CHECKOUT,
    )
    product = Product.objects.create(
        name="Test product in PLN channel",
        slug="test-product-8-pln",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_PLN,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=timezone.now(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_A_PLN")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_PLN.currency_code,
    )
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
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
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    product = Product.objects.create(
        name="Test product 2 in PLN channel",
        slug="test-product-9-pln",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_PLN,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=timezone.now(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_B_PLN")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(20),
        discounted_price_amount=Decimal(20),
        cost_price_amount=Decimal(2),
        currency=channel_PLN.currency_code,
    )
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=2
    )

    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 2
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
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
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    order.shipping_address = order.billing_address.get_copy()
    order.channel = channel_PLN
    shipping_method = shipping_method_channel_PLN
    shipping_price = shipping_method.channel_listings.get(
        channel_id=channel_PLN.id,
    )
    order.shipping_method_name = shipping_method.name
    order.shipping_method = shipping_method

    net = shipping_price.get_total()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order.shipping_price = TaxedMoney(net=net, gross=gross)
    order.base_shipping_price = net
    order.undiscounted_base_shipping_price = net
    order.shipping_tax_rate = calculate_tax_rate(order.shipping_price)
    order.save()

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_with_line_without_inventory_tracking(
    order, variant_without_inventory_tracking
):
    variant = variant_without_inventory_tracking
    product = variant.product
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    order.lines.create(
        product_name=str(variant.product),
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
        **get_tax_class_kwargs_for_order_line(product.product_type.tax_class),
    )

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_with_preorder_lines(
    order, product_type, category, shipping_zone, warehouse, channel_USD
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-8",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=timezone.now(),
    )
    variant = ProductVariant.objects.create(
        product=product, sku="SKU_AA_P", is_preorder=True
    )
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
        preorder_quantity_threshold=10,
    )

    net = variant.get_price(channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
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
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
    )
    PreorderAllocation.objects.create(
        order_line=line,
        product_variant_channel_listing=channel_listing,
        quantity=line.quantity,
    )

    order.shipping_address = order.billing_address.get_copy()
    order.channel = channel_USD
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_price = shipping_method.channel_listings.get(channel_id=channel_USD.id)
    order.shipping_method_name = shipping_method.name
    order.shipping_method = shipping_method

    net = shipping_price.get_total()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order.shipping_price = TaxedMoney(net=net, gross=gross)
    order.base_shipping_price = net
    order.undiscounted_base_shipping_price = net
    order.save()

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_events(order):
    order_events = [
        OrderEvent(type=event_type, order=order)
        for event_type, _ in OrderEvents.CHOICES
    ]
    OrderEvent.objects.bulk_create(order_events)
    return order_events


@pytest.fixture
def fulfilled_order(order_with_lines):
    order = order_with_lines
    order.invoices.create(
        url="http://www.example.com/invoice.pdf",
        number="01/12/2020/TEST",
        created_at=datetime.datetime.now(tz=datetime.UTC),
        status=JobStatus.SUCCESS,
    )
    fulfillment = order.fulfillments.create(tracking_number="123")
    line_1 = order.lines.first()
    stock_1 = line_1.allocations.get().stock
    warehouse_1_pk = stock_1.warehouse.pk
    line_2 = order.lines.last()
    stock_2 = line_2.allocations.get().stock
    warehouse_2_pk = stock_2.warehouse.pk
    fulfillment.lines.create(order_line=line_1, quantity=line_1.quantity, stock=stock_1)
    fulfillment.lines.create(order_line=line_2, quantity=line_2.quantity, stock=stock_2)
    fulfill_order_lines(
        [
            OrderLineInfo(
                line=line_1, quantity=line_1.quantity, warehouse_pk=warehouse_1_pk
            ),
            OrderLineInfo(
                line=line_2, quantity=line_2.quantity, warehouse_pk=warehouse_2_pk
            ),
        ],
        manager=get_plugins_manager(allow_replica=False),
    )
    order.status = OrderStatus.FULFILLED
    order.save(update_fields=["status"])
    return order


@pytest.fixture
def unconfirmed_order_with_lines(order_with_lines):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    return order


@pytest.fixture
def fulfilled_order_without_inventory_tracking(
    order_with_line_without_inventory_tracking,
):
    order = order_with_line_without_inventory_tracking
    fulfillment = order.fulfillments.create(tracking_number="123")
    line = order.lines.first()
    stock = line.variant.stocks.get()
    warehouse_pk = stock.warehouse.pk
    fulfillment.lines.create(order_line=line, quantity=line.quantity, stock=stock)
    fulfill_order_lines(
        [OrderLineInfo(line=line, quantity=line.quantity, warehouse_pk=warehouse_pk)],
        get_plugins_manager(allow_replica=False),
    )
    order.status = OrderStatus.FULFILLED
    order.save(update_fields=["status"])
    return order


@pytest.fixture
def fulfilled_order_with_cancelled_fulfillment(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.create()
    line_1 = fulfilled_order.lines.first()
    line_2 = fulfilled_order.lines.last()
    fulfillment.lines.create(order_line=line_1, quantity=line_1.quantity)
    fulfillment.lines.create(order_line=line_2, quantity=line_2.quantity)
    fulfillment.status = FulfillmentStatus.CANCELED
    fulfillment.save()
    return fulfilled_order


@pytest.fixture
def fulfilled_order_with_all_cancelled_fulfillments(
    fulfilled_order, staff_user, warehouse
):
    fulfillment = fulfilled_order.fulfillments.get()
    cancel_fulfillment(
        fulfillment,
        staff_user,
        None,
        warehouse,
        get_plugins_manager(allow_replica=False),
    )
    return fulfilled_order


@pytest.fixture
def order_with_digital_line(order, digital_content, stock, site_settings):
    site_settings.automatic_fulfillment_digital_products = True
    site_settings.save()

    variant = stock.product_variant
    variant.digital_content = digital_content
    variant.digital_content.save()

    product_type = variant.product.product_type
    product_type.is_shipping_required = False
    product_type.is_digital = True
    product_type.save()

    quantity = 3
    product = variant.product
    channel = order.channel
    variant_channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(variant_channel_listing)
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
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
        tax_rate=Decimal("0.23"),
    )

    Allocation.objects.create(order_line=line, stock=stock, quantity_allocated=quantity)

    return order


@pytest.fixture
@freeze_time("2021-11-01 12:00:01")
def preorders(orders, product):
    variants = [
        ProductVariant(
            product=product,
            is_preorder=True,
            sku=f"Preorder product variant #{i}",
        )
        for i in (1, 2, 3, 4)
    ]
    variants[1].preorder_end_date = timezone.now() + timedelta(days=1)
    variants[2].preorder_end_date = timezone.now()
    variants[3].preorder_end_date = timezone.now() - timedelta(days=1)
    ProductVariant.objects.bulk_create(variants)

    lines = [
        OrderLine(
            order=order,
            product_name=str(product),
            variant_name=str(variant),
            product_sku=variant.sku,
            product_variant_id=variant.get_global_id(),
            is_shipping_required=variant.is_shipping_required(),
            is_gift_card=variant.is_gift_card(),
            quantity=1,
            variant=variant,
            unit_price_net_amount=Decimal("10.0"),
            unit_price_gross_amount=Decimal("10.0"),
            currency="USD",
            total_price_net_amount=Decimal("10.0"),
            total_price_gross_amount=Decimal("10.0"),
            undiscounted_unit_price_net_amount=Decimal("10.0"),
            undiscounted_unit_price_gross_amount=Decimal("10.0"),
            undiscounted_total_price_net_amount=Decimal("10.0"),
            undiscounted_total_price_gross_amount=Decimal("10.0"),
        )
        for variant, order in zip(variants, orders)
    ]
    OrderLine.objects.bulk_create(lines)
    preorders = orders[: len(variants) - 1]
    return preorders
