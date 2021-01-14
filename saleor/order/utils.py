from decimal import Decimal
from functools import wraps
from typing import Iterable, List

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from prices import Money, TaxedMoney

from ..account.models import User
from ..core.taxes import zero_money
from ..core.weight import zero_weight
from ..discount.models import NotApplicable, Voucher, VoucherType
from ..discount.utils import get_products_voucher_discount, validate_voucher_in_order
from ..order import OrderStatus
from ..order.models import Order, OrderLine
from ..plugins.manager import get_plugins_manager
from ..product.utils.digital_products import get_default_digital_content_settings
from ..shipping.models import ShippingMethod
from ..warehouse.management import deallocate_stock, increase_stock
from ..warehouse.models import Warehouse
from . import events


def get_order_country(order: Order) -> str:
    """Return country to which order will be shipped."""
    address = order.billing_address
    if order.is_shipping_required():
        address = order.shipping_address
    if address is None:
        return settings.DEFAULT_COUNTRY
    return address.country.code


def order_line_needs_automatic_fulfillment(line: OrderLine) -> bool:
    """Check if given line is digital and should be automatically fulfilled."""
    digital_content_settings = get_default_digital_content_settings()
    default_automatic_fulfillment = digital_content_settings["automatic_fulfillment"]
    content = line.variant.digital_content if line.variant else None
    if not content:
        return False
    if default_automatic_fulfillment and content.use_default_settings:
        return True
    if content.automatic_fulfillment:
        return True
    return False


def order_needs_automatic_fulfillment(order: Order) -> bool:
    """Check if order has digital products which should be automatically fulfilled."""
    for line in order.lines.digital():
        if order_line_needs_automatic_fulfillment(line):
            return True
    return False


def update_voucher_discount(func):
    """Recalculate order discount amount based on order voucher."""

    @wraps(func)
    def decorator(*args, **kwargs):
        if kwargs.pop("update_voucher_discount", True):
            order = args[0]
            try:
                discount = get_voucher_discount_for_order(order)
            except NotApplicable:
                discount = zero_money(order.currency)
            order.discount = discount
        return func(*args, **kwargs)

    return decorator


@update_voucher_discount
def recalculate_order(order: Order, **kwargs):
    """Recalculate and assign total price of order.

    Total price is a sum of items in order and order shipping price minus
    discount amount.

    Voucher discount amount is recalculated by default. To avoid this, pass
    update_voucher_discount argument set to False.
    """
    # avoid using prefetched order lines
    lines = [OrderLine.objects.get(pk=line.pk) for line in order]
    prices = [line.total_price for line in lines]
    total = sum(prices, order.shipping_price)
    # discount amount can't be greater than order total
    order.discount_amount = min(order.discount_amount, total.gross.amount)
    if order.discount:
        total -= order.discount
    order.total = total
    order.save(
        update_fields=[
            "discount_amount",
            "total_net_amount",
            "total_gross_amount",
            "currency",
        ]
    )
    recalculate_order_weight(order)


def recalculate_order_weight(order):
    """Recalculate order weights."""
    weight = zero_weight()
    for line in order:
        if line.variant:
            weight += line.variant.get_weight() * line.quantity
    order.weight = weight
    order.save(update_fields=["weight"])


def update_order_prices(order, discounts):
    """Update prices in order with given discounts and proper taxes."""
    manager = get_plugins_manager()
    channel = order.channel
    for line in order:  # type: OrderLine
        if line.variant:
            product = line.variant.product
            channel_listing = line.variant.channel_listings.get(channel=channel)
            collections = product.collections.all()
            unit_price = line.variant.get_price(
                product, collections, channel, channel_listing, discounts
            )
            unit_price = TaxedMoney(unit_price, unit_price)
            line.unit_price = unit_price
            line.save(
                update_fields=[
                    "currency",
                    "unit_price_net_amount",
                    "unit_price_gross_amount",
                ]
            )

            price = manager.calculate_order_line_unit(line)
            if price != line.unit_price:
                line.unit_price = price
                if price.tax and price.net:
                    line.tax_rate = manager.get_order_line_tax_rate(
                        order, product, None, price
                    )
                line.save()

    if order.shipping_method:
        shipping_price = manager.calculate_order_shipping(order)
        order.shipping_price = shipping_price
        order.shipping_tax_rate = manager.get_order_shipping_tax_rate(
            order, shipping_price
        )
        order.save(
            update_fields=[
                "shipping_price_net_amount",
                "shipping_price_gross_amount",
                "shipping_tax_rate",
                "currency",
            ]
        )

    recalculate_order(order)


def update_order_status(order):
    """Update order status depending on fulfillments."""
    quantity_fulfilled = order.quantity_fulfilled
    total_quantity = order.get_total_quantity()

    if quantity_fulfilled <= 0:
        status = OrderStatus.UNFULFILLED
    elif quantity_fulfilled < total_quantity:
        status = OrderStatus.PARTIALLY_FULFILLED
    else:
        status = OrderStatus.FULFILLED

    if status != order.status:
        order.status = status
        order.save(update_fields=["status"])


@transaction.atomic
def add_variant_to_draft_order(order, variant, quantity, discounts=None):
    """Add total_quantity of variant to order.

    Returns an order line the variant was added to.
    """
    try:
        line = order.lines.get(variant=variant)
        line.quantity += quantity
        line.save(update_fields=["quantity"])
    except OrderLine.DoesNotExist:
        product = variant.product
        collections = product.collections.all()
        channel = order.channel
        channel_listing = variant.channel_listings.get(channel=channel)
        unit_price = variant.get_price(
            product, collections, channel, channel_listing, discounts
        )
        unit_price = TaxedMoney(net=unit_price, gross=unit_price)
        total_price = unit_price * quantity
        product_name = str(product)
        variant_name = str(variant)
        translated_product_name = str(product.translated)
        translated_variant_name = str(variant.translated)
        if translated_product_name == product_name:
            translated_product_name = ""
        if translated_variant_name == variant_name:
            translated_variant_name = ""
        line = order.lines.create(
            product_name=product_name,
            variant_name=variant_name,
            translated_product_name=translated_product_name,
            translated_variant_name=translated_variant_name,
            product_sku=variant.sku,
            is_shipping_required=variant.is_shipping_required(),
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            variant=variant,
        )
        manager = get_plugins_manager()
        unit_price = manager.calculate_order_line_unit(line)
        line.unit_price = unit_price
        line.tax_rate = manager.get_order_line_tax_rate(
            order, product, None, unit_price
        )
        line.save(
            update_fields=[
                "currency",
                "unit_price_net_amount",
                "unit_price_gross_amount",
                "tax_rate",
            ]
        )

    return line


def add_gift_card_to_order(order, gift_card, total_price_left):
    """Add gift card to order.

    Return a total price left after applying the gift cards.
    """
    if total_price_left > zero_money(total_price_left.currency):
        order.gift_cards.add(gift_card)
        if total_price_left < gift_card.current_balance:
            gift_card.current_balance = gift_card.current_balance - total_price_left
            total_price_left = zero_money(total_price_left.currency)
        else:
            total_price_left = total_price_left - gift_card.current_balance
            gift_card.current_balance_amount = 0
        gift_card.last_used_on = timezone.now()
        gift_card.save(update_fields=["current_balance_amount", "last_used_on"])
    return total_price_left


def change_order_line_quantity(user, line, old_quantity, new_quantity):
    """Change the quantity of ordered items in a order line."""
    if new_quantity:
        line.quantity = new_quantity
        total_price_net_amount = line.quantity * line.unit_price_net_amount
        total_price_gross_amount = line.quantity * line.unit_price_gross_amount
        line.total_price_net_amount = total_price_net_amount.quantize(Decimal("0.001"))
        line.total_price_gross_amount = total_price_gross_amount.quantize(
            Decimal("0.001")
        )
        line.save(
            update_fields=[
                "quantity",
                "total_price_net_amount",
                "total_price_gross_amount",
            ]
        )
    else:
        delete_order_line(line)

    quantity_diff = old_quantity - new_quantity

    # Create the removal event
    if quantity_diff > 0:
        events.draft_order_removed_products_event(
            order=line.order, user=user, order_lines=[(quantity_diff, line)]
        )
    elif quantity_diff < 0:
        events.draft_order_added_products_event(
            order=line.order, user=user, order_lines=[(quantity_diff * -1, line)]
        )


def delete_order_line(line):
    """Delete an order line from an order."""
    line.delete()


def restock_order_lines(order):
    """Return ordered products to corresponding stocks."""
    country = get_order_country(order)
    default_warehouse = Warehouse.objects.filter(
        shipping_zones__countries__contains=country
    ).first()

    for line in order:
        if line.variant and line.variant.track_inventory:
            if line.quantity_unfulfilled > 0:
                deallocate_stock(line, line.quantity_unfulfilled)
            if line.quantity_fulfilled > 0:
                allocation = line.allocations.first()
                warehouse = (
                    allocation.stock.warehouse if allocation else default_warehouse
                )
                increase_stock(line, warehouse, line.quantity_fulfilled)

        if line.quantity_fulfilled > 0:
            line.quantity_fulfilled = 0
            line.save(update_fields=["quantity_fulfilled"])


def restock_fulfillment_lines(fulfillment, warehouse):
    """Return fulfilled products to corresponding stocks.

    Return products to stocks and update order lines quantity fulfilled values.
    """
    order_lines = []
    for line in fulfillment:
        if line.order_line.variant and line.order_line.variant.track_inventory:
            increase_stock(line.order_line, warehouse, line.quantity, allocate=True)
        order_line = line.order_line
        order_line.quantity_fulfilled -= line.quantity
        order_lines.append(order_line)
    OrderLine.objects.bulk_update(order_lines, ["quantity_fulfilled"])


def sum_order_totals(qs, currency_code):
    zero = Money(0, currency=currency_code)
    taxed_zero = TaxedMoney(zero, zero)
    return sum([order.total for order in qs], taxed_zero)


def get_valid_shipping_methods_for_order(order: Order):
    if not order.is_shipping_required():
        return None
    if not order.shipping_address:
        return None
    return ShippingMethod.objects.applicable_shipping_methods_for_instance(
        order,
        channel_id=order.channel_id,
        price=order.get_subtotal().gross,
        country_code=order.shipping_address.country.code,
    )


def get_discounted_lines(lines, voucher):
    discounted_products = voucher.products.all()
    discounted_categories = set(voucher.categories.all())
    discounted_collections = set(voucher.collections.all())

    discounted_lines = []
    if discounted_products or discounted_collections or discounted_categories:
        for line in lines:
            line_product = line.variant.product
            line_category = line.variant.product.category
            line_collections = set(line.variant.product.collections.all())
            if line.variant and (
                line_product in discounted_products
                or line_category in discounted_categories
                or line_collections.intersection(discounted_collections)
            ):
                discounted_lines.append(line)
    else:
        # If there's no discounted products, collections or categories,
        # it means that all products are discounted
        discounted_lines.extend(list(lines))
    return discounted_lines


def get_prices_of_discounted_specific_product(
    lines: Iterable[OrderLine],
    voucher: Voucher,
) -> List[Money]:
    """Get prices of variants belonging to the discounted specific products.

    Specific products are products, collections and categories.
    Product must be assigned directly to the discounted category, assigning
    product to child category won't work.
    """
    line_prices = []
    discounted_lines = get_discounted_lines(lines, voucher)

    for line in discounted_lines:
        line_prices.extend([line.unit_price_gross] * line.quantity)

    return line_prices


def get_products_voucher_discount_for_order(order: Order) -> Money:
    """Calculate products discount value for a voucher, depending on its type."""
    prices = None
    voucher = order.voucher
    if voucher and voucher.type == VoucherType.SPECIFIC_PRODUCT:
        prices = get_prices_of_discounted_specific_product(order.lines.all(), voucher)
    if not prices:
        msg = "This offer is only valid for selected items."
        raise NotApplicable(msg)
    return get_products_voucher_discount(voucher, prices, order.channel)  # type: ignore


def get_voucher_discount_for_order(order: Order) -> Money:
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    if not order.voucher:
        return zero_money(order.currency)
    validate_voucher_in_order(order)
    subtotal = order.get_subtotal()
    if order.voucher.type == VoucherType.ENTIRE_ORDER:
        return order.voucher.get_discount_amount_for(subtotal.gross, order.channel)
    if order.voucher.type == VoucherType.SHIPPING:
        return order.voucher.get_discount_amount_for(
            order.shipping_price, order.channel
        )
    if order.voucher.type == VoucherType.SPECIFIC_PRODUCT:
        return get_products_voucher_discount_for_order(order)
    raise NotImplementedError("Unknown discount type")


def match_orders_with_new_user(user: User) -> None:
    Order.objects.confirmed().filter(user_email=user.email, user=None).update(user=user)
