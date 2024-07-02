from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, cast

from django.conf import settings
from django.db.models import QuerySet, Sum
from django.utils import timezone
from prices import Money, TaxedMoney

from ..account.models import User
from ..core.prices import quantize_price
from ..core.taxes import zero_money
from ..core.tracing import traced_atomic_transaction
from ..core.utils.country import get_active_country
from ..core.utils.translations import get_translation
from ..core.weight import zero_weight
from ..discount import DiscountType, DiscountValueType
from ..discount.models import (
    OrderDiscount,
    OrderLineDiscount,
    VoucherType,
)
from ..discount.utils.manual_discount import (
    apply_discount_to_value,
)
from ..discount.utils.promotion import (
    get_discount_name,
    get_discount_translated_name,
    get_sale_id,
    prepare_promotion_discount_reason,
)
from ..giftcard import events as gift_card_events
from ..giftcard.models import GiftCard
from ..giftcard.search import mark_gift_cards_search_index_as_dirty
from ..payment import TransactionEventType
from ..payment.model_helpers import get_total_authorized
from ..product.utils.digital_products import get_default_digital_content_settings
from ..shipping.interface import ShippingMethodData
from ..shipping.models import ShippingMethod, ShippingMethodChannelListing
from ..shipping.utils import (
    convert_to_shipping_method_data,
    initialize_shipping_method_active_status,
)
from ..tax.utils import get_display_gross_prices, get_tax_class_kwargs_for_order_line
from ..warehouse.management import (
    decrease_allocations,
    get_order_lines_with_track_inventory,
    increase_allocations,
    increase_stock,
)
from ..warehouse.models import Warehouse
from . import (
    ORDER_EDITABLE_STATUS,
    FulfillmentStatus,
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderGrantedRefundStatus,
    OrderStatus,
    events,
)
from .fetch import OrderLineInfo
from .models import Order, OrderGrantedRefund, OrderLine

if TYPE_CHECKING:
    from ..app.models import App
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutInfo
    from ..discount.interface import VariantPromotionRuleInfo
    from ..payment.models import Payment, TransactionItem
    from ..plugins.manager import PluginsManager


def get_order_country(order: Order) -> str:
    """Return country to which order will be shipped."""
    return get_active_country(
        order.channel, order.shipping_address, order.billing_address
    )


def order_line_needs_automatic_fulfillment(line_data: OrderLineInfo) -> bool:
    """Check if given line is digital and should be automatically fulfilled."""
    digital_content_settings = get_default_digital_content_settings()
    default_automatic_fulfillment = digital_content_settings["automatic_fulfillment"]
    content = line_data.digital_content
    if not content:
        return False
    if default_automatic_fulfillment and content.use_default_settings:
        return True
    if content.automatic_fulfillment:
        return True
    return False


def order_needs_automatic_fulfillment(lines_data: Iterable["OrderLineInfo"]) -> bool:
    """Check if order has digital products which should be automatically fulfilled."""
    for line_data in lines_data:
        if line_data.is_digital and order_line_needs_automatic_fulfillment(line_data):
            return True
    return False


def get_voucher_discount_assigned_to_order(order: Order):
    return order.discounts.filter(type=DiscountType.VOUCHER).first()


def invalidate_order_prices(order: Order, *, save: bool = False) -> None:
    """Mark order as ready for prices recalculation.

    Does nothing if order is not editable
    (it's status is neither draft, nor unconfirmed).

    By default, no save to database is executed.
    Either manually call `order.save()` after, or pass `save=True`.
    """
    if order.status not in ORDER_EDITABLE_STATUS:
        return

    order.should_refresh_prices = True

    if save:
        order.save(update_fields=["should_refresh_prices"])


def recalculate_order_weight(order: Order, *, save: bool = False):
    """Recalculate order weights.

    By default, no save to database is executed.
    Either manually call `order.save()` after, or pass `save=True`.
    """
    weight = zero_weight()
    for line in order.lines.all():
        if line.variant:
            weight += line.variant.get_weight() * line.quantity
    weight.unit = order.weight.unit
    order.weight = weight
    if save:
        order.save(update_fields=["weight", "updated_at"])


def _calculate_quantity_including_returns(order):
    lines = list(order.lines.all())
    total_quantity = sum([line.quantity for line in lines])
    quantity_fulfilled = sum([line.quantity_fulfilled for line in lines])
    quantity_returned = 0
    quantity_replaced = 0
    for fulfillment in order.fulfillments.all():
        # count returned quantity for order
        if fulfillment.status in [
            FulfillmentStatus.RETURNED,
            FulfillmentStatus.REFUNDED_AND_RETURNED,
        ]:
            quantity_returned += fulfillment.get_total_quantity()
        # count replaced quantity for order
        elif fulfillment.status == FulfillmentStatus.REPLACED:
            quantity_replaced += fulfillment.get_total_quantity()

    # Subtract the replace quantity as it shouldn't be taken into consideration for
    # calculating the order status
    total_quantity -= quantity_replaced
    quantity_fulfilled -= quantity_replaced
    return total_quantity, quantity_fulfilled, quantity_returned


def update_order_status(order: Order):
    """Update order status depending on fulfillments."""
    (
        total_quantity,
        quantity_fulfilled,
        quantity_returned,
    ) = _calculate_quantity_including_returns(order)

    # check if order contains any fulfillments that awaiting approval
    awaiting_approval = order.fulfillments.filter(
        status=FulfillmentStatus.WAITING_FOR_APPROVAL
    ).exists()

    # total_quantity == 0 means that all products have been replaced, we don't change
    # the order status in that case
    if total_quantity == 0:
        status = order.status
    elif quantity_fulfilled <= 0:
        status = OrderStatus.UNFULFILLED
    elif 0 < quantity_returned < total_quantity:
        status = OrderStatus.PARTIALLY_RETURNED
    elif quantity_returned == total_quantity:
        status = OrderStatus.RETURNED
    elif quantity_fulfilled < total_quantity or awaiting_approval:
        status = OrderStatus.PARTIALLY_FULFILLED
    else:
        status = OrderStatus.FULFILLED

    if status != order.status:
        order.status = status
        order.save(update_fields=["status", "updated_at"])


@traced_atomic_transaction()
def create_order_line(
    order,
    line_data,
    manager,
    allocate_stock=False,
):
    channel = order.channel
    variant = line_data.variant
    quantity = line_data.quantity
    price_override = line_data.price_override
    rules_info = line_data.rules_info

    product = variant.product
    channel_listing = variant.channel_listings.get(channel=channel)

    # vouchers are not applied for new lines in unconfirmed/draft orders
    untaxed_unit_price = variant.get_price(
        channel_listing,
        price_override=price_override,
        promotion_rules=(
            [rule_info.rule for rule_info in rules_info] if rules_info else None
        ),
    )
    untaxed_undiscounted_price = variant.get_base_price(
        channel_listing,
        price_override=price_override,
    )
    unit_price = TaxedMoney(net=untaxed_unit_price, gross=untaxed_unit_price)
    undiscounted_unit_price = TaxedMoney(
        net=untaxed_undiscounted_price, gross=untaxed_undiscounted_price
    )
    total_price = unit_price * quantity
    undiscounted_total_price = undiscounted_unit_price * quantity

    tax_class = None
    if product.tax_class_id:
        tax_class = product.tax_class
    else:
        tax_class = product.product_type.tax_class

    product_name = str(product)
    variant_name = str(variant)
    language_code = order.language_code
    translated_product_name = get_translation(product, language_code).name
    translated_variant_name = get_translation(variant, language_code).name
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
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        unit_price=unit_price,
        undiscounted_unit_price=undiscounted_unit_price,
        base_unit_price=untaxed_unit_price,
        undiscounted_base_unit_price=untaxed_undiscounted_price,
        total_price=total_price,
        undiscounted_total_price=undiscounted_total_price,
        variant=variant,
        is_price_overridden=price_override is not None,
        **get_tax_class_kwargs_for_order_line(tax_class),
    )

    unit_discount = line.undiscounted_unit_price - line.unit_price
    if unit_discount.gross:
        if rules_info:
            line_discounts = create_order_line_discounts(line, rules_info)
            promotion = rules_info[0].promotion
            line.sale_id = get_sale_id(promotion)
            line.unit_discount_reason = (
                prepare_promotion_discount_reason(promotion, line.sale_id)
                if line_discounts
                else None
            )

        tax_configuration = channel.tax_configuration
        prices_entered_with_tax = tax_configuration.prices_entered_with_tax

        if prices_entered_with_tax:
            discount_amount = unit_discount.gross
        else:
            discount_amount = unit_discount.net
        line.unit_discount = discount_amount
        line.unit_discount_type = DiscountValueType.FIXED
        line.unit_discount_value = discount_amount.amount

        line.save(
            update_fields=[
                "unit_discount_amount",
                "unit_discount_value",
                "unit_discount_reason",
                "unit_discount_type",
                "sale_id",
            ]
        )

    if allocate_stock:
        increase_allocations(
            [
                OrderLineInfo(
                    line=line,
                    quantity=quantity,
                    variant=variant,
                    warehouse_pk=None,
                )
            ],
            channel,
            manager=manager,
        )

    return line


def create_order_line_discounts(
    line: "OrderLine", rules_info: Iterable["VariantPromotionRuleInfo"]
) -> Iterable["OrderLineDiscount"]:
    line_discounts_to_create: list[OrderLineDiscount] = []
    for rule_info in rules_info:
        rule = rule_info.rule
        if not rule_info.variant_listing_promotion_rule:
            continue
        rule_discount_amount = rule_info.variant_listing_promotion_rule.discount_amount
        line_discounts_to_create.append(
            OrderLineDiscount(
                line=line,
                type=DiscountType.PROMOTION,
                value_type=rule.reward_value_type,
                value=rule.reward_value,
                amount_value=rule_discount_amount,
                currency=line.currency,
                name=get_discount_name(rule, rule_info.promotion),
                translated_name=get_discount_translated_name(rule_info),
                reason=None,
                promotion_rule=rule,
            )
        )

    return OrderLineDiscount.objects.bulk_create(line_discounts_to_create)


@traced_atomic_transaction()
def add_variant_to_order(
    order,
    line_data,
    user,
    app,
    manager,
    allocate_stock=False,
):
    """Add total_quantity of variant to order.

    Returns an order line the variant was added to.
    """
    channel = order.channel

    if line_data.line_id:
        line = order.lines.get(pk=line_data.line_id)
        old_quantity = line.quantity
        new_quantity = old_quantity + line_data.quantity
        line_info = OrderLineInfo(line=line, quantity=old_quantity)
        update_fields: list[str] = []
        if new_quantity and line_data.price_override is not None:
            update_line_base_unit_prices_with_custom_price(
                order, line_data, line, update_fields
            )

        change_order_line_quantity(
            user,
            app,
            line_info,
            old_quantity,
            new_quantity,
            channel,
            manager=manager,
            send_event=False,
            update_fields=update_fields,
        )

        if update_fields:
            line.save(update_fields=update_fields)

        if allocate_stock:
            increase_allocations(
                [
                    OrderLineInfo(
                        line=line,
                        quantity=line_data.quantity,
                        variant=line_data.variant,
                        warehouse_pk=None,
                    )
                ],
                channel,
                manager=manager,
            )

        return line

    if line_data.variant_id:
        return create_order_line(
            order,
            line_data,
            manager,
            allocate_stock,
        )


def update_line_base_unit_prices_with_custom_price(
    order, line_data, line, update_fields
):
    channel = order.channel
    variant = line_data.variant
    price_override = line_data.price_override
    rules_info = line_data.rules_info
    channel_listing = variant.channel_listings.get(channel=channel)

    line.is_price_overridden = True
    line.base_unit_price = variant.get_price(
        channel_listing,
        price_override=price_override,
        promotion_rules=(
            [rule_info.rule for rule_info in rules_info] if rules_info else None
        ),
    )
    line.undiscounted_base_unit_price_amount = price_override
    line.undiscounted_unit_price_gross_amount = price_override
    line.undiscounted_unit_price_net_amount = price_override

    update_fields.extend(
        [
            "is_price_overridden",
            "undiscounted_base_unit_price_amount",
            "base_unit_price_amount",
            "undiscounted_unit_price_gross_amount",
            "undiscounted_unit_price_net_amount",
        ]
    )


def add_gift_cards_to_order(
    checkout_info: "CheckoutInfo",
    order: Order,
    total_price_left: Money,
    user: Optional[User],
    app: Optional["App"],
):
    order_gift_cards = []
    gift_cards_to_update = []
    balance_data: list[tuple[GiftCard, float]] = []
    used_by_user = checkout_info.user
    used_by_email = cast(str, checkout_info.get_customer_email())
    for gift_card in checkout_info.checkout.gift_cards.select_for_update():
        if total_price_left > zero_money(total_price_left.currency):
            order_gift_cards.append(gift_card)

            total_price_left = update_gift_card_balance(
                gift_card, total_price_left, balance_data
            )

            set_gift_card_user(gift_card, used_by_user, used_by_email)

            gift_card.last_used_on = timezone.now()
            gift_cards_to_update.append(gift_card)

    order.gift_cards.add(*order_gift_cards)
    update_fields = [
        "current_balance_amount",
        "last_used_on",
        "used_by",
        "used_by_email",
    ]
    GiftCard.objects.bulk_update(gift_cards_to_update, update_fields)
    gift_card_events.gift_cards_used_in_order_event(balance_data, order, user, app)


def update_gift_card_balance(
    gift_card: GiftCard,
    total_price_left: Money,
    balance_data: list[tuple[GiftCard, float]],
) -> Money:
    previous_balance = gift_card.current_balance
    if total_price_left < gift_card.current_balance:
        gift_card.current_balance = gift_card.current_balance - total_price_left
        total_price_left = zero_money(total_price_left.currency)
    else:
        total_price_left = total_price_left - gift_card.current_balance
        gift_card.current_balance_amount = 0
    balance_data.append((gift_card, previous_balance.amount))
    return total_price_left


def set_gift_card_user(
    gift_card: GiftCard,
    used_by_user: Optional[User],
    used_by_email: str,
):
    """Set the user, each time a giftcard is used."""
    gift_card.used_by = (
        used_by_user
        if used_by_user
        else User.objects.filter(email=used_by_email).first()
    )
    gift_card.used_by_email = used_by_email
    mark_gift_cards_search_index_as_dirty([gift_card])


def _update_allocations_for_line(
    line_info: OrderLineInfo,
    old_quantity: int,
    new_quantity: int,
    channel: "Channel",
    manager: "PluginsManager",
):
    if old_quantity == new_quantity:
        return

    if not get_order_lines_with_track_inventory([line_info]):
        return

    if old_quantity < new_quantity:
        line_info.quantity = new_quantity - old_quantity
        increase_allocations([line_info], channel, manager)
    else:
        line_info.quantity = old_quantity - new_quantity
        decrease_allocations([line_info], manager)


def change_order_line_quantity(
    user,
    app,
    line_info,
    old_quantity: int,
    new_quantity: int,
    channel: "Channel",
    manager: "PluginsManager",
    send_event=True,
    update_fields=None,
):
    """Change the quantity of ordered items in a order line."""
    line = line_info.line
    if new_quantity:
        if line.order.is_unconfirmed():
            _update_allocations_for_line(
                line_info, old_quantity, new_quantity, channel, manager
            )
        line.quantity = new_quantity
        total_price_net_amount = line.quantity * line.unit_price_net_amount
        total_price_gross_amount = line.quantity * line.unit_price_gross_amount
        line.total_price_net_amount = total_price_net_amount.quantize(Decimal("0.001"))
        line.total_price_gross_amount = total_price_gross_amount.quantize(
            Decimal("0.001")
        )
        undiscounted_total_price_gross_amount = (
            line.quantity * line.undiscounted_unit_price_gross_amount
        )
        undiscounted_total_price_net_amount = (
            line.quantity * line.undiscounted_unit_price_net_amount
        )
        line.undiscounted_total_price_gross_amount = (
            undiscounted_total_price_gross_amount.quantize(Decimal("0.001"))
        )
        line.undiscounted_total_price_net_amount = (
            undiscounted_total_price_net_amount.quantize(Decimal("0.001"))
        )
        fields = [
            "quantity",
            "total_price_net_amount",
            "total_price_gross_amount",
            "undiscounted_total_price_gross_amount",
            "undiscounted_total_price_net_amount",
        ]
        if update_fields:
            update_fields.extend(fields)
        else:
            line.save(update_fields=fields)
    else:
        delete_order_line(line_info, manager)

    quantity_diff = old_quantity - new_quantity

    if send_event:
        create_order_event(line, user, app, quantity_diff)


def create_order_event(line, user, app, quantity_diff):
    if quantity_diff > 0:
        events.order_removed_products_event(
            order=line.order,
            user=user,
            app=app,
            order_lines=[line],
            quantity_diff=quantity_diff,
        )
    elif quantity_diff < 0:
        events.order_added_products_event(
            order=line.order,
            user=user,
            app=app,
            order_lines=[line],
            quantity_diff=quantity_diff * -1,
        )


def delete_order_line(line_info, manager):
    """Delete an order line from an order."""
    if line_info.line.order.is_unconfirmed():
        decrease_allocations([line_info], manager)
    line_info.line.delete()


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
    totals = qs.aggregate(net=Sum("total_net_amount"), gross=Sum("total_gross_amount"))
    return TaxedMoney(
        Money(totals["net"] or 0, currency=currency_code),
        Money(totals["gross"] or 0, currency=currency_code),
    )


def get_all_shipping_methods_for_order(
    order: Order,
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> list[ShippingMethodData]:
    if not order.is_shipping_required():
        return []

    shipping_address = order.shipping_address
    if not shipping_address:
        return []

    all_methods = []

    shipping_methods = (
        ShippingMethod.objects.using(database_connection_name)
        .applicable_shipping_methods_for_instance(
            order,
            channel_id=order.channel_id,
            price=order.subtotal.gross,
            shipping_address=shipping_address,
            country_code=shipping_address.country.code,
        )
        .prefetch_related("channel_listings")
    )

    listing_map = {
        listing.shipping_method_id: listing for listing in shipping_channel_listings
    }

    for method in shipping_methods:
        listing = listing_map.get(method.id)
        if listing:
            shipping_method_data = convert_to_shipping_method_data(method, listing)
            all_methods.append(shipping_method_data)
    return all_methods


def get_valid_shipping_methods_for_order(
    order: Order,
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"],
    manager: "PluginsManager",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> list[ShippingMethodData]:
    """Return a list of shipping methods according to Saleor's own business logic."""
    valid_methods = get_all_shipping_methods_for_order(
        order, shipping_channel_listings, database_connection_name
    )
    if not valid_methods:
        return []

    excluded_methods = manager.excluded_shipping_methods_for_order(order, valid_methods)
    initialize_shipping_method_active_status(valid_methods, excluded_methods)

    return valid_methods


def is_shipping_required(lines: Iterable["OrderLine"]):
    return any(line.is_shipping_required for line in lines)


def get_total_quantity(lines: Iterable["OrderLine"]):
    return sum([line.quantity for line in lines])


def get_valid_collection_points_for_order(
    lines: Iterable["OrderLine"],
    channel_id: int,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    if not is_shipping_required(lines):
        return []

    line_ids = [line.id for line in lines]
    qs = OrderLine.objects.using(database_connection_name).filter(id__in=line_ids)

    return Warehouse.objects.using(
        database_connection_name
    ).applicable_for_click_and_collect(qs, channel_id)


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


def match_orders_with_new_user(user: User) -> None:
    Order.objects.confirmed().filter(user_email=user.email, user=None).update(user=user)


def get_total_order_discount(order: Order) -> Money:
    """Return total order discount assigned to the order."""
    all_discounts = order.discounts.all()
    total_order_discount = Money(
        sum([discount.amount_value for discount in all_discounts]),
        currency=order.currency,
    )
    total_order_discount = min(total_order_discount, order.undiscounted_total_gross)
    return total_order_discount


def get_total_order_discount_excluding_shipping(order: Order) -> Money:
    """Return total discounts assigned to the order excluding shipping discounts."""
    # If the order has an assigned shipping voucher we want to exclude the corresponding
    # order discount from the calculation.
    # The calculation is based on assumption that an order can have only one voucher.
    all_discounts = order.discounts.all()
    if order.voucher and order.voucher.type == VoucherType.SHIPPING:
        all_discounts = all_discounts.exclude(type=DiscountType.VOUCHER)
    total_order_discount = Money(
        sum([discount.amount_value for discount in all_discounts]),
        currency=order.currency,
    )
    total_order_discount = min(total_order_discount, order.undiscounted_total_gross)
    return total_order_discount


def get_order_discounts(order: Order) -> list[OrderDiscount]:
    """Return all discounts applied to the order by staff user."""
    return list(order.discounts.filter(type=DiscountType.MANUAL))


def create_order_discount_for_order(
    order: Order,
    reason: str,
    value_type: str,
    value: Decimal,
    type: Optional[str] = None,
):
    """Add new order discount and update the prices."""

    current_total = order.undiscounted_total
    currency = order.currency

    gross_total = apply_discount_to_value(
        value, value_type, currency, current_total.gross
    )

    new_amount = quantize_price((current_total - gross_total).gross, currency)
    kwargs = {} if not type else {"type": type}

    order_discount = order.discounts.create(
        value_type=value_type,
        value=value,
        reason=reason,
        amount=new_amount,  # type: ignore
        **kwargs,
    )
    return order_discount


def remove_order_discount_from_order(order: Order, order_discount: OrderDiscount):
    """Remove the order discount from order and update the prices."""

    discount_amount = order_discount.amount
    order_discount.delete()

    order.total += discount_amount
    order.save(update_fields=["total_net_amount", "total_gross_amount", "updated_at"])


def update_discount_for_order_line(
    order_line: OrderLine,
    order: "Order",
    reason: Optional[str],
    value_type: Optional[str],
    value: Optional[Decimal],
):
    """Update discount fields for order line. Apply discount to the price."""
    # TODO: Move price calculation to fetch_order_prices_if_expired function.
    # Here we should only create order line discount object
    # https://github.com/saleor/saleor/issues/15517
    current_value = order_line.unit_discount_value
    current_value_type = order_line.unit_discount_type
    value = value or current_value
    value_type = value_type or current_value_type
    fields_to_update = []
    if reason is not None:
        order_line.unit_discount_reason = reason
        fields_to_update.append("unit_discount_reason")

    if current_value != value or current_value_type != value_type:
        undiscounted_base_unit_price = order_line.undiscounted_base_unit_price
        currency = undiscounted_base_unit_price.currency
        base_unit_price = apply_discount_to_value(
            value, value_type, currency, undiscounted_base_unit_price
        )

        order_line.unit_discount = undiscounted_base_unit_price - base_unit_price

        order_line.unit_price = TaxedMoney(base_unit_price, base_unit_price)
        order_line.base_unit_price = base_unit_price

        order_line.unit_discount_type = value_type
        order_line.unit_discount_value = value
        # TODO: should we save those values?
        order_line.total_price = order_line.unit_price * order_line.quantity
        order_line.undiscounted_unit_price = (
            order_line.unit_price + order_line.unit_discount
        )
        order_line.undiscounted_total_price = (
            order_line.quantity * order_line.undiscounted_unit_price
        )
        fields_to_update.extend(
            [
                "tax_rate",
                "unit_discount_value",
                "unit_discount_amount",
                "unit_discount_type",
                "unit_discount_reason",
                "unit_price_gross_amount",
                "unit_price_net_amount",
                "total_price_net_amount",
                "total_price_gross_amount",
                "base_unit_price_amount",
                "undiscounted_unit_price_gross_amount",
                "undiscounted_unit_price_net_amount",
                "undiscounted_total_price_gross_amount",
                "undiscounted_total_price_net_amount",
            ]
        )

    # Save lines before calculating the taxes as some plugin can fetch all order data
    # from db
    order_line.save(update_fields=fields_to_update)

    _update_manual_order_line_discount_object(
        value, value_type, reason, order_line, order.currency
    )


def _update_manual_order_line_discount_object(
    value, value_type, reason, order_line, currency
):
    discount_to_update = None
    discount_to_delete_ids = []
    discounts = order_line.discounts.all()
    for discount in discounts:
        if discount.type == DiscountType.MANUAL and not discount_to_update:
            discount_to_update = discount
        elif discount.type != DiscountType.VOUCHER:
            discount_to_delete_ids.append(discount.pk)

    if discount_to_delete_ids:
        OrderLineDiscount.objects.filter(id__in=discount_to_delete_ids).delete()

    amount_value = quantize_price(
        order_line.unit_discount.amount * order_line.quantity, currency
    )
    if not discount_to_update:
        order_line.discounts.create(
            type=DiscountType.MANUAL,
            value_type=value_type,
            value=value,
            amount_value=amount_value,
            currency=currency,
            reason=reason,
            unique_type=DiscountType.MANUAL,
        )
    else:
        update_fields = []
        if discount_to_update.value_type != value_type:
            discount_to_update.value_type = value_type
            update_fields.append("value_type")
        if discount_to_update.value != value:
            discount_to_update.value = value
            discount_to_update.amount_value = amount_value
            update_fields.extend(["value", "amount_value"])
        if discount_to_update.reason != reason:
            discount_to_update.reason = reason
            update_fields.append("reason")
        discount_to_update.save(update_fields=update_fields)


def remove_discount_from_order_line(order_line: OrderLine, order: "Order"):
    """Drop discount applied to order line. Restore undiscounted price."""
    order_line.unit_price = TaxedMoney(
        net=order_line.undiscounted_base_unit_price,
        gross=order_line.undiscounted_base_unit_price,
    )
    order_line.base_unit_price = order_line.undiscounted_base_unit_price
    order_line.undiscounted_unit_price = TaxedMoney(
        net=order_line.undiscounted_base_unit_price,
        gross=order_line.undiscounted_base_unit_price,
    )
    order_line.unit_discount_amount = Decimal(0)
    order_line.unit_discount_value = Decimal(0)
    order_line.unit_discount_reason = ""
    order_line.total_price = order_line.unit_price * order_line.quantity
    order_line.save(
        update_fields=[
            "unit_discount_value",
            "unit_discount_amount",
            "unit_discount_reason",
            "unit_price_gross_amount",
            "unit_price_net_amount",
            "base_unit_price_amount",
            "total_price_net_amount",
            "total_price_gross_amount",
            "tax_rate",
        ]
    )
    order_line.discounts.all().delete()


def update_order_charge_status(order: Order, granted_refund_amount: Decimal):
    """Update the current charge status for the order.

    We treat the order as overcharged when the charged amount is bigger that
    order.total - order granted refund
    We treat the order as fully charged when the charged amount is equal to
    order.total - order granted refund.
    We treat the order as partially charged when the charged amount covers only part of
    the order.total - order granted refund
    We treat the order as not charged when the charged amount is 0.
    """
    total_charged = order.total_charged_amount or Decimal("0")
    total_charged = quantize_price(total_charged, order.currency)

    current_total_gross = order.total_gross_amount - granted_refund_amount
    current_total_gross = max(current_total_gross, Decimal("0"))
    current_total_gross = quantize_price(current_total_gross, order.currency)

    if total_charged == current_total_gross:
        order.charge_status = OrderChargeStatus.FULL
    elif total_charged <= Decimal(0):
        order.charge_status = OrderChargeStatus.NONE
    elif total_charged < current_total_gross:
        order.charge_status = OrderChargeStatus.PARTIAL
    else:
        order.charge_status = OrderChargeStatus.OVERCHARGED


def _update_order_total_charged(
    order: Order,
    order_payments: QuerySet["Payment"],
    order_transactions: Iterable["TransactionItem"],
):
    order.total_charged_amount = sum(
        [p.captured_amount for p in order_payments], Decimal(0)
    )
    order.total_charged_amount += sum([tr.charged_value for tr in order_transactions])


def update_order_charge_data(
    order: Order,
    order_payments: Optional[QuerySet["Payment"]] = None,
    order_transactions: Optional[QuerySet["TransactionItem"]] = None,
    order_granted_refunds: Optional[QuerySet["OrderGrantedRefund"]] = None,
    with_save=True,
):
    if order_payments is None:
        order_payments = order.payments.all()
    if order_transactions is None:
        order_transactions = order.payment_transactions.all()
    if order_granted_refunds is None:
        order_granted_refunds = order.granted_refunds.all()
    granted_refund_amount = sum(
        [refund.amount.amount for refund in order_granted_refunds], Decimal(0)
    )
    _update_order_total_charged(
        order, order_payments=order_payments, order_transactions=order_transactions
    )
    update_order_charge_status(order, granted_refund_amount)
    if with_save:
        order.save(
            update_fields=["total_charged_amount", "charge_status", "updated_at"]
        )


def _update_order_total_authorized(
    order: Order,
    order_payments: QuerySet["Payment"],
    order_transactions: QuerySet["TransactionItem"],
):
    order.total_authorized_amount = get_total_authorized(
        order_payments, order.currency
    ).amount
    order.total_authorized_amount += sum(
        [tr.authorized_value for tr in order_transactions]
    )


def update_order_authorize_status(order: Order, granted_refund_amount: Decimal):
    """Update the current authorize status for the order.

    The order is fully authorized when total_authorized or total_charged funds
    cover the order.total - order granted refunds
    The order is partially authorized when total_authorized or total_charged
    funds cover only part of the order.total - order granted refunds
    The order is not authorized when total_authorized and total_charged funds are 0.
    """
    total_covered = (
        order.total_authorized_amount + order.total_charged_amount
    ) or Decimal(0)
    total_covered = quantize_price(total_covered, order.currency)
    current_total_gross = order.total_gross_amount - granted_refund_amount
    current_total_gross = max(current_total_gross, Decimal("0"))
    current_total_gross = quantize_price(current_total_gross, order.currency)

    if total_covered == Decimal(0) and order.total.gross.amount == Decimal(0):
        order.authorize_status = OrderAuthorizeStatus.FULL
    elif total_covered == Decimal(0):
        order.authorize_status = OrderAuthorizeStatus.NONE
    elif total_covered >= current_total_gross:
        order.authorize_status = OrderAuthorizeStatus.FULL
    else:
        order.authorize_status = OrderAuthorizeStatus.PARTIAL


def update_order_authorize_data(
    order: Order,
    order_payments: Optional[QuerySet["Payment"]] = None,
    order_transactions: Optional[QuerySet["TransactionItem"]] = None,
    order_granted_refunds: Optional[QuerySet["OrderGrantedRefund"]] = None,
    with_save=True,
):
    if order_payments is None:
        order_payments = order.payments.all()
    if order_transactions is None:
        order_transactions = order.payment_transactions.all()
    if order_granted_refunds is None:
        order_granted_refunds = order.granted_refunds.all()
    granted_refund_amount = sum(
        [refund.amount.amount for refund in order_granted_refunds]
    )
    _update_order_total_authorized(
        order, order_payments=order_payments, order_transactions=order_transactions
    )
    update_order_authorize_status(order, granted_refund_amount)
    if with_save:
        order.save(
            update_fields=["total_authorized_amount", "authorize_status", "updated_at"]
        )


def updates_amounts_for_order(order: Order, save: bool = True):
    order_payments = order.payments.all()
    order_transactions = order.payment_transactions.all()
    order_granted_refunds = order.granted_refunds.all()
    update_order_charge_data(
        order=order,
        order_payments=order_payments,
        order_transactions=order_transactions,
        order_granted_refunds=order_granted_refunds,
        with_save=False,
    )
    update_order_authorize_data(
        order=order,
        order_payments=order_payments,
        order_transactions=order_transactions,
        order_granted_refunds=order_granted_refunds,
        with_save=False,
    )
    if save:
        order.save(
            update_fields=[
                "total_charged_amount",
                "charge_status",
                "updated_at",
                "total_authorized_amount",
                "authorize_status",
            ]
        )


def update_order_display_gross_prices(order: "Order"):
    """Update Order's `display_gross_prices` DB field.

    It gets the appropriate country code based on the current order lines and addresses.
    Having the country code get the proper tax configuration for this channel and
    country and determine whether gross prices should be displayed for this order.
    Doesn't save the value in the database.
    """
    channel = order.channel
    tax_configuration = channel.tax_configuration
    country_code = get_active_country(
        channel,
        order.shipping_address,
        order.billing_address,
    )
    country_tax_configuration = tax_configuration.country_exceptions.filter(
        country=country_code
    ).first()
    order.display_gross_prices = get_display_gross_prices(
        tax_configuration, country_tax_configuration
    )


def calculate_order_granted_refund_status(
    granted_refund: OrderGrantedRefund,
    with_save: bool = True,
):
    """Update the status for the granted refund.

    The status is calculated based on last transaction event related to refund action.
    """

    last_event = (
        granted_refund.transaction_events.filter(
            transaction_id=granted_refund.transaction_item_id,
            type__in=[
                TransactionEventType.REFUND_REQUEST,
                TransactionEventType.REFUND_SUCCESS,
                TransactionEventType.REFUND_REVERSE,
                TransactionEventType.REFUND_FAILURE,
            ],
        )
        .order_by("created_at")
        .last()
    )

    current_granted_refund_status = granted_refund.status
    if not last_event:
        return
    if last_event.type == TransactionEventType.REFUND_SUCCESS:
        granted_refund.status = OrderGrantedRefundStatus.SUCCESS
    elif last_event.type == TransactionEventType.REFUND_REQUEST:
        granted_refund.status = OrderGrantedRefundStatus.PENDING
    elif last_event.type == TransactionEventType.REFUND_FAILURE:
        granted_refund.status = OrderGrantedRefundStatus.FAILURE
    else:
        granted_refund.status = OrderGrantedRefundStatus.NONE

    if with_save and current_granted_refund_status != granted_refund.status:
        granted_refund.save(update_fields=["status"])


def log_address_if_validation_skipped_for_order(order: "Order", logger):
    address = get_address_for_order_taxes(order)
    if address and address.validation_skipped:
        logger.warning(
            "Fetching tax data for order with address validation skipped. "
            "Address ID: %s",
            address.id,
        )


def get_address_for_order_taxes(order: "Order"):
    if order.collection_point_id:
        address = order.collection_point.address  # type: ignore[union-attr]
    else:
        address = order.shipping_address or order.billing_address
    return address
