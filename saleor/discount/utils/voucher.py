from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, cast

from django.db.models import Exists, F, OuterRef
from django.utils import timezone
from prices import Money

from ...channel.models import Channel
from ...core.taxes import zero_money
from ...core.utils.promo_code import InvalidPromoCode
from ...order.models import Order
from .. import (
    DiscountType,
    VoucherType,
)
from ..models import (
    DiscountValueType,
    NotApplicable,
    OrderLineDiscount,
    Voucher,
    VoucherCode,
    VoucherCustomer,
)
from .shared import update_line_discount

if TYPE_CHECKING:
    from ...account.models import User
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...core.pricing.interface import LineInfo
    from ...order.fetch import EditableOrderLineInfo
    from ...order.models import OrderLine
    from ...plugins.manager import PluginsManager
    from ..interface import VoucherInfo
    from ..models import Voucher


def is_order_level_voucher(voucher: Optional[Voucher]):
    return bool(
        voucher
        and voucher.type == VoucherType.ENTIRE_ORDER
        and not voucher.apply_once_per_order
    )


def increase_voucher_usage(
    voucher: "Voucher",
    code: "VoucherCode",
    customer_email: Optional[str],
    increase_voucher_customer_usage: bool = True,
) -> None:
    if voucher.usage_limit:
        increase_voucher_code_usage_value(code)
    if voucher.apply_once_per_customer and increase_voucher_customer_usage:
        add_voucher_usage_by_customer(code, customer_email)
    if voucher.single_use:
        deactivate_voucher_code(code)


def increase_voucher_code_usage_value(code: "VoucherCode") -> None:
    """Increase voucher code uses by 1."""
    code.used = F("used") + 1
    code.save(update_fields=["used"])


def decrease_voucher_code_usage_value(code: "VoucherCode") -> None:
    """Decrease voucher code uses by 1."""
    code.used = F("used") - 1
    code.save(update_fields=["used"])


def deactivate_voucher_code(code: "VoucherCode") -> None:
    """Mark voucher code as used."""
    code.is_active = False
    code.save(update_fields=["is_active"])


def activate_voucher_code(code: "VoucherCode") -> None:
    """Mark voucher code as unused."""
    code.is_active = True
    code.save(update_fields=["is_active"])


def add_voucher_usage_by_customer(
    code: "VoucherCode", customer_email: Optional[str]
) -> None:
    if not customer_email:
        raise NotApplicable("Unable to apply voucher as customer details are missing.")

    _, created = VoucherCustomer.objects.get_or_create(
        voucher_code=code, customer_email=customer_email
    )
    if not created:
        raise NotApplicable("This offer is only valid once per customer.")


def remove_voucher_usage_by_customer(code: "VoucherCode", customer_email: str) -> None:
    voucher_customer = VoucherCustomer.objects.filter(
        voucher_code=code, customer_email=customer_email
    )
    if voucher_customer:
        voucher_customer.delete()


def release_voucher_code_usage(
    code: Optional["VoucherCode"],
    voucher: Optional["Voucher"],
    user_email: Optional[str],
):
    if not code:
        return
    if voucher and voucher.usage_limit:
        decrease_voucher_code_usage_value(code)
    if voucher and voucher.single_use:
        activate_voucher_code(code)
    if user_email:
        remove_voucher_usage_by_customer(code, user_email)


def get_voucher_code_instance(
    voucher_code: str,
    channel_slug: str,
):
    """Return a voucher code instance if it's valid or raise an error."""
    if (
        Voucher.objects.active_in_channel(
            date=timezone.now(), channel_slug=channel_slug
        )
        .filter(
            Exists(
                VoucherCode.objects.filter(
                    code=voucher_code,
                    voucher_id=OuterRef("id"),
                    is_active=True,
                )
            )
        )
        .exists()
    ):
        code_instance = VoucherCode.objects.get(code=voucher_code)
    else:
        raise InvalidPromoCode()
    return code_instance


def get_active_voucher_code(voucher, channel_slug):
    """Return an active VoucherCode instance.

    This method along with `Voucher.code` should be removed in Saleor 4.0.
    """

    voucher_queryset = Voucher.objects.active_in_channel(timezone.now(), channel_slug)
    if not voucher_queryset.filter(pk=voucher.pk).exists():
        raise InvalidPromoCode()
    voucher_code = VoucherCode.objects.filter(voucher=voucher, is_active=True).first()
    if not voucher_code:
        raise InvalidPromoCode()
    return voucher_code


def apply_voucher_to_line(
    voucher_info: "VoucherInfo",
    lines_info: Iterable["LineInfo"],
):
    """Attach voucher to valid checkout or order lines info.

    Apply a voucher to checkout/order line info when the voucher has the type
    SPECIFIC_PRODUCTS or is applied only to the cheapest item.
    """
    voucher = voucher_info.voucher
    discounted_lines_by_voucher: list[LineInfo] = []
    lines_included_in_discount = lines_info
    if voucher.type == VoucherType.SPECIFIC_PRODUCT:
        discounted_lines_by_voucher.extend(
            get_discounted_lines(lines_info, voucher_info)
        )
        lines_included_in_discount = discounted_lines_by_voucher
    if voucher.apply_once_per_order:
        if cheapest_line := _get_the_cheapest_line(lines_included_in_discount):
            discounted_lines_by_voucher = [cheapest_line]
    for line_info in lines_info:
        if line_info in discounted_lines_by_voucher:
            line_info.voucher = voucher
            line_info.voucher_code = voucher_info.voucher_code


def get_discounted_lines(
    lines: Iterable["LineInfo"], voucher_info: "VoucherInfo"
) -> Iterable["LineInfo"]:
    discounted_lines = []
    if (
        voucher_info.product_pks
        or voucher_info.collection_pks
        or voucher_info.category_pks
        or voucher_info.variant_pks
    ):
        for line_info in lines:
            if line_info.line.is_gift:
                continue
            line_variant = line_info.variant
            line_product = line_info.product
            if not line_variant or not line_product:
                continue
            line_category = line_product.category
            line_collections = set(
                [collection.pk for collection in line_info.collections]
            )
            if line_info.variant and (
                line_variant.pk in voucher_info.variant_pks
                or line_product.pk in voucher_info.product_pks
                or line_category
                and line_category.pk in voucher_info.category_pks
                or line_collections.intersection(voucher_info.collection_pks)
            ):
                discounted_lines.append(line_info)
    else:
        # If there's no discounted products, collections or categories,
        # it means that all products are discounted
        discounted_lines.extend(lines)
    return discounted_lines


def _get_the_cheapest_line(
    lines_info: Optional[Iterable["LineInfo"]],
) -> Optional["LineInfo"]:
    if not lines_info:
        return None
    return min(
        lines_info, key=lambda line_info: line_info.channel_listing.discounted_price
    )


def validate_voucher_for_checkout(
    manager: "PluginsManager",
    voucher: "Voucher",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
):
    from ...checkout import base_calculations
    from ...checkout.utils import calculate_checkout_quantity

    quantity = calculate_checkout_quantity(lines)
    subtotal = base_calculations.base_checkout_subtotal(
        lines,
        checkout_info.channel,
        checkout_info.checkout.currency,
    )

    customer_email = cast(str, checkout_info.get_customer_email())
    validate_voucher(
        voucher,
        subtotal,
        quantity,
        customer_email,
        checkout_info.channel,
        checkout_info.user,
    )


def validate_voucher_in_order(
    order: "Order", lines: Iterable["OrderLine"], channel: "Channel"
):
    if not order.voucher:
        return

    from ...order.utils import get_total_quantity

    subtotal = order.subtotal
    quantity = get_total_quantity(lines)
    customer_email = order.get_customer_email()
    tax_configuration = channel.tax_configuration
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    value = subtotal.gross if prices_entered_with_tax else subtotal.net

    validate_voucher(
        order.voucher, value, quantity, customer_email, channel, order.user
    )


def validate_voucher(
    voucher: "Voucher",
    total_price: Money,
    quantity: int,
    customer_email: str,
    channel: Channel,
    customer: Optional["User"],
) -> None:
    voucher.validate_min_spent(total_price, channel)
    voucher.validate_min_checkout_items_quantity(quantity)
    if voucher.apply_once_per_customer:
        voucher.validate_once_per_customer(customer_email)
    if voucher.only_for_staff:
        voucher.validate_only_for_staff(customer)


def get_products_voucher_discount(
    voucher: "Voucher", prices: Iterable[Money], channel: Channel
) -> Money:
    """Calculate discount value for a voucher of product or category type."""
    if voucher.apply_once_per_order:
        return voucher.get_discount_amount_for(min(prices), channel)
    discounts = (voucher.get_discount_amount_for(price, channel) for price in prices)
    total_amount = sum(discounts, zero_money(channel.currency_code))
    return total_amount


def create_or_update_line_discount_objects_from_voucher(order, lines_info):
    """Create or update line discount object for voucher applied on lines.

    The LineDiscount object is created for each line with voucher applied.
    Only `SPECIFIC_PRODUCT` and `apply_once_per_order` voucher types are applied.

    """
    # FIXME: temporary - create_order_line_discount_objects should be moved to shared
    from .order import create_order_line_discount_objects

    discount_data = prepare_line_discount_objects_for_voucher(lines_info)
    modified_lines_info = create_order_line_discount_objects(lines_info, discount_data)
    # base unit price must reflect all actual line voucher discounts
    if modified_lines_info:
        _reduce_base_unit_price_for_voucher_discount(modified_lines_info)


# TODO (SHOPX-912): share the method with checkout
def prepare_line_discount_objects_for_voucher(
    lines_info: Iterable["EditableOrderLineInfo"],
):
    line_discounts_to_create_inputs: list[dict] = []
    line_discounts_to_update: list[OrderLineDiscount] = []
    line_discounts_to_remove: list[OrderLineDiscount] = []
    updated_fields: list[str] = []

    if not lines_info:
        return

    for line_info in lines_info:
        line = line_info.line
        total_price = line.base_unit_price * line.quantity
        discount_amount = calculate_line_discount_amount_from_voucher(
            line_info, total_price
        )
        # only one voucher can be applied
        discount_to_update = None
        if discounts_to_update := line_info.get_voucher_discounts():
            discount_to_update = discounts_to_update[0]

        if not discount_amount or line.is_gift:
            if discount_to_update:
                line_discounts_to_remove.append(discount_to_update)
            continue

        discount_amount = discount_amount.amount
        discount_reason = f"Voucher code: {line_info.voucher_code}"
        voucher = cast(Voucher, line_info.voucher)
        discount_name = f"{voucher.name}"
        if discount_to_update:
            update_line_discount(
                None,
                voucher,
                discount_name,
                # TODO (SHOPX-914): set translated voucher name
                "",
                discount_reason,
                discount_amount,
                # TODO (SHOPX-914): should be taken from voucher value_type and value
                discount_amount,
                DiscountValueType.FIXED,
                DiscountType.VOUCHER,
                discount_to_update,
                updated_fields,
            )
            line_discounts_to_update.append(discount_to_update)
        else:
            line_discount_input = {
                "line": line,
                "type": DiscountType.VOUCHER,
                # TODO (SHOPX-914): should be taken from voucher value_type and value
                "value_type": DiscountValueType.FIXED,
                "value": discount_amount,
                "amount_value": discount_amount,
                "currency": line.currency,
                "name": discount_name,
                "translated_name": None,
                "reason": discount_reason,
                "voucher": line_info.voucher,
                "unique_type": DiscountType.VOUCHER,
            }
            line_discounts_to_create_inputs.append(line_discount_input)

    return (
        line_discounts_to_create_inputs,
        line_discounts_to_update,
        line_discounts_to_remove,
        updated_fields,
    )


def calculate_line_discount_amount_from_voucher(
    line_info: "LineInfo", total_price: Money
) -> Money:
    """Calculate discount amount for voucher applied on line.

    Included vouchers: `SPECIFIC_PRODUCT` and `apply_once_per_order`.

    Args:
        line_info: Order/Checkout line data.
        total_price: Total price of the line, should be already reduced by
    catalogue discounts if any applied.

    """
    if not line_info.voucher:
        return zero_money(total_price.currency)

    channel = line_info.channel
    quantity = line_info.line.quantity
    if not line_info.voucher.apply_once_per_order:
        if line_info.voucher.discount_value_type == DiscountValueType.PERCENTAGE:
            voucher_discount_amount = line_info.voucher.get_discount_amount_for(
                total_price, channel=channel
            )
            discount_amount = min(voucher_discount_amount, total_price)
        else:
            unit_price = total_price / quantity
            voucher_unit_discount_amount = line_info.voucher.get_discount_amount_for(
                unit_price, channel=channel
            )
            discount_amount = min(
                voucher_unit_discount_amount * quantity,
                total_price,
            )
    else:
        unit_price = total_price / quantity
        voucher_unit_discount_amount = line_info.voucher.get_discount_amount_for(
            unit_price, channel=channel
        )
        discount_amount = min(voucher_unit_discount_amount, unit_price)
    return discount_amount


def _reduce_base_unit_price_for_voucher_discount(
    lines_info: Iterable["EditableOrderLineInfo"],
):
    for line_info in lines_info:
        line = line_info.line
        base_unit_price = line.base_unit_price_amount
        for discount in line_info.get_voucher_discounts():
            base_unit_price -= discount.amount_value / line.quantity
        line.base_unit_price_amount = max(base_unit_price, Decimal(0))
