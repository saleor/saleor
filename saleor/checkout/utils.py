"""Checkout-related utility functions."""
from typing import Iterable, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db.models import Max, Min, Sum
from django.utils import timezone
from prices import Money, MoneyRange, TaxedMoneyRange

from ..account.models import User
from ..checkout import calculations
from ..checkout.error_codes import CheckoutErrorCode
from ..core.exceptions import ProductNotPublished
from ..core.prices import quantize_price
from ..core.taxes import zero_taxed_money
from ..core.utils.promo_code import (
    InvalidPromoCode,
    promo_code_is_gift_card,
    promo_code_is_voucher,
)
from ..discount import DiscountInfo, VoucherType
from ..discount.models import NotApplicable, Voucher
from ..discount.utils import (
    get_discounted_lines,
    get_products_voucher_discount,
    validate_voucher_for_checkout,
)
from ..giftcard.utils import (
    add_gift_card_code_to_checkout,
    remove_gift_card_code_from_checkout,
)
from ..plugins.manager import get_plugins_manager
from ..shipping.models import ShippingMethod
from ..warehouse.availability import check_stock_quantity
from . import AddressType
from .models import Checkout, CheckoutLine


def get_user_checkout(
    user: User, checkout_queryset=Checkout.objects.all(), auto_create=False
) -> Tuple[Optional[Checkout], bool]:
    """Return an active checkout for given user or None if no auto create.

    If auto create is enabled, it will retrieve an active checkout or create it
    (safer for concurrency).
    """
    if auto_create:
        return checkout_queryset.get_or_create(
            user=user,
            defaults={
                "shipping_address": user.default_shipping_address,
                "billing_address": user.default_billing_address,
            },
        )
    return checkout_queryset.filter(user=user).first(), False


def update_checkout_quantity(checkout):
    """Update the total quantity in checkout."""
    total_lines = checkout.lines.aggregate(total_quantity=Sum("quantity"))[
        "total_quantity"
    ]
    if not total_lines:
        total_lines = 0
    checkout.quantity = total_lines
    checkout.save(update_fields=["quantity"])


def check_variant_in_stock(
    checkout, variant, quantity=1, replace=False, check_quantity=True
) -> Tuple[int, Optional[CheckoutLine]]:
    """Check if a given variant is in stock and return the new quantity + line."""
    line = checkout.lines.filter(variant=variant).first()
    line_quantity = 0 if line is None else line.quantity

    new_quantity = quantity if replace else (quantity + line_quantity)

    if new_quantity < 0:
        raise ValueError(
            "%r is not a valid quantity (results in %r)" % (quantity, new_quantity)
        )

    if new_quantity > 0 and check_quantity:
        check_stock_quantity(variant, checkout.get_country(), new_quantity)

    return new_quantity, line


def add_variant_to_checkout(
    checkout, variant, quantity=1, replace=False, check_quantity=True
):
    """Add a product variant to checkout.

    If `replace` is truthy then any previous quantity is discarded instead
    of added to.
    """
    if not variant.product.is_published:
        raise ProductNotPublished()

    new_quantity, line = check_variant_in_stock(
        checkout,
        variant,
        quantity=quantity,
        replace=replace,
        check_quantity=check_quantity,
    )

    if line is None:
        line = checkout.lines.filter(variant=variant).first()

    if new_quantity == 0:
        if line is not None:
            line.delete()
    elif line is None:
        checkout.lines.create(checkout=checkout, variant=variant, quantity=new_quantity)
    elif new_quantity > 0:
        line.quantity = new_quantity
        line.save(update_fields=["quantity"])

    update_checkout_quantity(checkout)


def _check_new_checkout_address(checkout, address, address_type):
    """Check if and address in checkout has changed and if to remove old one."""
    if address_type == AddressType.BILLING:
        old_address = checkout.billing_address
    else:
        old_address = checkout.shipping_address

    has_address_changed = any(
        [
            not address and old_address,
            address and not old_address,
            address and old_address and address != old_address,
        ]
    )

    remove_old_address = (
        has_address_changed
        and old_address is not None
        and (not checkout.user or old_address not in checkout.user.addresses.all())
    )

    return has_address_changed, remove_old_address


def change_billing_address_in_checkout(checkout, address):
    """Save billing address in checkout if changed.

    Remove previously saved address if not connected to any user.
    """
    changed, remove = _check_new_checkout_address(
        checkout, address, AddressType.BILLING
    )
    if changed:
        if remove:
            checkout.billing_address.delete()
        checkout.billing_address = address
        checkout.save(update_fields=["billing_address", "last_change"])


def change_shipping_address_in_checkout(checkout, address):
    """Save shipping address in checkout if changed.

    Remove previously saved address if not connected to any user.
    """
    changed, remove = _check_new_checkout_address(
        checkout, address, AddressType.SHIPPING
    )
    if changed:
        if remove:
            checkout.shipping_address.delete()
        checkout.shipping_address = address
        checkout.save(update_fields=["shipping_address", "last_change"])


def _get_shipping_voucher_discount_for_checkout(
    voucher, checkout, lines, discounts: Optional[Iterable[DiscountInfo]] = None
):
    """Calculate discount value for a voucher of shipping type."""
    if not checkout.is_shipping_required():
        msg = "Your order does not require shipping."
        raise NotApplicable(msg)
    shipping_method = checkout.shipping_method
    if not shipping_method:
        msg = "Please select a shipping method first."
        raise NotApplicable(msg)

    # check if voucher is limited to specified countries
    shipping_country = checkout.shipping_address.country
    if voucher.countries and shipping_country.code not in voucher.countries:
        msg = "This offer is not valid in your country."
        raise NotApplicable(msg)

    shipping_price = calculations.checkout_shipping_price(
        checkout=checkout, lines=lines, discounts=discounts
    ).gross
    return voucher.get_discount_amount_for(shipping_price)


def _get_products_voucher_discount(
    lines, voucher, discounts: Optional[Iterable[DiscountInfo]] = None
):
    """Calculate products discount value for a voucher, depending on its type."""
    prices = None
    if voucher.type == VoucherType.SPECIFIC_PRODUCT:
        prices = get_prices_of_discounted_specific_product(lines, voucher, discounts)
    if not prices:
        msg = "This offer is only valid for selected items."
        raise NotApplicable(msg)
    return get_products_voucher_discount(voucher, prices)


def get_prices_of_discounted_specific_product(
    lines: List[CheckoutLine],
    voucher: Voucher,
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> List[Money]:
    """Get prices of variants belonging to the discounted specific products.

    Specific products are products, collections and categories.
    Product must be assigned directly to the discounted category, assigning
    product to child category won't work.
    """
    line_prices = []
    discounted_lines = get_discounted_lines(lines, voucher)
    for line in discounted_lines:
        line_total = calculations.checkout_line_total(
            line=line, discounts=discounts or []
        ).gross
        line_unit_price = quantize_price(
            (line_total / line.quantity), line_total.currency
        )
        line_prices.extend([line_unit_price] * line.quantity)

    return line_prices


def get_voucher_discount_for_checkout(
    voucher: Voucher,
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> Money:
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    validate_voucher_for_checkout(voucher, checkout, lines, discounts)
    if voucher.type == VoucherType.ENTIRE_ORDER:
        subtotal = calculations.checkout_subtotal(
            checkout=checkout, lines=lines, discounts=discounts
        ).gross
        return voucher.get_discount_amount_for(subtotal)
    if voucher.type == VoucherType.SHIPPING:
        return _get_shipping_voucher_discount_for_checkout(
            voucher, checkout, lines, discounts
        )
    if voucher.type == VoucherType.SPECIFIC_PRODUCT:
        return _get_products_voucher_discount(lines, voucher, discounts)
    raise NotImplementedError("Unknown discount type")


def get_voucher_for_checkout(
    checkout: Checkout, vouchers=None, with_lock: bool = False
) -> Optional[Voucher]:
    """Return voucher with voucher code saved in checkout if active or None."""
    if checkout.voucher_code is not None:
        if vouchers is None:
            vouchers = Voucher.objects.active(date=timezone.now())
        try:
            qs = vouchers
            if with_lock:
                qs = vouchers.select_for_update()
            return qs.get(code=checkout.voucher_code)
        except Voucher.DoesNotExist:
            return None
    return None


def recalculate_checkout_discount(
    checkout: Checkout, lines: Iterable[CheckoutLine], discounts: Iterable[DiscountInfo]
):
    """Recalculate `checkout.discount` based on the voucher.

    Will clear both voucher and discount if the discount is no longer
    applicable.
    """
    voucher = get_voucher_for_checkout(checkout)
    if voucher is not None:
        try:
            discount = get_voucher_discount_for_checkout(
                voucher, checkout, lines, discounts
            )
        except NotApplicable:
            remove_voucher_from_checkout(checkout)
        else:
            subtotal = calculations.checkout_subtotal(
                checkout=checkout, lines=lines, discounts=discounts
            ).gross
            checkout.discount = (
                min(discount, subtotal)
                if voucher.type != VoucherType.SHIPPING
                else discount
            )
            checkout.discount_name = str(voucher)
            checkout.translated_discount_name = (
                voucher.translated.name
                if voucher.translated.name != voucher.name
                else ""
            )
            checkout.save(
                update_fields=[
                    "translated_discount_name",
                    "discount_amount",
                    "discount_name",
                    "currency",
                ]
            )
    else:
        remove_voucher_from_checkout(checkout)


def add_promo_code_to_checkout(
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    promo_code: str,
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    """Add gift card or voucher data to checkout.

    Raise InvalidPromoCode if promo code does not match to any voucher or gift card.
    """
    if promo_code_is_voucher(promo_code):
        add_voucher_code_to_checkout(checkout, lines, promo_code, discounts)
    elif promo_code_is_gift_card(promo_code):
        add_gift_card_code_to_checkout(checkout, promo_code)
    else:
        raise InvalidPromoCode()


def add_voucher_code_to_checkout(
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    voucher_code: str,
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    """Add voucher data to checkout by code.

    Raise InvalidPromoCode() if voucher of given type cannot be applied.
    """
    try:
        voucher = Voucher.objects.active(date=timezone.now()).get(code=voucher_code)
    except Voucher.DoesNotExist:
        raise InvalidPromoCode()
    try:
        add_voucher_to_checkout(checkout, lines, voucher, discounts)
    except NotApplicable:
        raise ValidationError(
            {
                "promo_code": ValidationError(
                    "Voucher is not applicable to that checkout.",
                    code=CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.value,
                )
            }
        )


def add_voucher_to_checkout(
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    voucher: Voucher,
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    """Add voucher data to checkout.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    discount = get_voucher_discount_for_checkout(voucher, checkout, lines, discounts)
    checkout.voucher_code = voucher.code
    checkout.discount_name = voucher.name
    checkout.translated_discount_name = (
        voucher.translated.name if voucher.translated.name != voucher.name else ""
    )
    checkout.discount = discount
    checkout.save(
        update_fields=[
            "voucher_code",
            "discount_name",
            "translated_discount_name",
            "discount_amount",
        ]
    )


def remove_promo_code_from_checkout(checkout: Checkout, promo_code: str):
    """Remove gift card or voucher data from checkout."""
    if promo_code_is_voucher(promo_code):
        remove_voucher_code_from_checkout(checkout, promo_code)
    elif promo_code_is_gift_card(promo_code):
        remove_gift_card_code_from_checkout(checkout, promo_code)


def remove_voucher_code_from_checkout(checkout: Checkout, voucher_code: str):
    """Remove voucher data from checkout by code."""
    existing_voucher = get_voucher_for_checkout(checkout)
    if existing_voucher and existing_voucher.code == voucher_code:
        remove_voucher_from_checkout(checkout)


def remove_voucher_from_checkout(checkout: Checkout):
    """Remove voucher data from checkout."""
    checkout.voucher_code = None
    checkout.discount_name = None
    checkout.translated_discount_name = None
    checkout.discount_amount = 0
    checkout.save(
        update_fields=[
            "voucher_code",
            "discount_name",
            "translated_discount_name",
            "discount_amount",
            "currency",
        ]
    )


def get_valid_shipping_methods_for_checkout(
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    discounts: Iterable[DiscountInfo],
    country_code: Optional[str] = None,
):
    manager = get_plugins_manager()
    return ShippingMethod.objects.applicable_shipping_methods_for_instance(
        checkout,
        price=manager.calculate_checkout_subtotal(checkout, lines, discounts).gross,
        country_code=country_code,
    )


def is_valid_shipping_method(
    checkout: Checkout, lines: Iterable[CheckoutLine], discounts: Iterable[DiscountInfo]
):
    """Check if shipping method is valid and remove (if not)."""
    if not checkout.shipping_method:
        return False

    valid_methods = get_valid_shipping_methods_for_checkout(checkout, lines, discounts)
    if valid_methods is None or checkout.shipping_method not in valid_methods:
        clear_shipping_method(checkout)
        return False
    return True


def get_shipping_price_estimate(
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    discounts: Iterable[DiscountInfo],
    country_code: str,
) -> Optional[TaxedMoneyRange]:
    """Return the estimated price range for shipping for given order."""

    shipping_methods = get_valid_shipping_methods_for_checkout(
        checkout, lines, discounts, country_code=country_code
    )

    if shipping_methods is None:
        return None

    # TODO: extension manager should be able to have impact on shipping price estimates
    min_price_amount, max_price_amount = shipping_methods.aggregate(
        price_amount_min=Min("price_amount"), price_amount_max=Max("price_amount")
    ).values()

    if min_price_amount is None:
        return None

    manager = get_plugins_manager()
    prices = MoneyRange(
        start=Money(min_price_amount, checkout.currency),
        stop=Money(max_price_amount, checkout.currency),
    )
    return manager.apply_taxes_to_shipping_price_range(prices, country_code)


def clear_shipping_method(checkout: Checkout):
    checkout.shipping_method = None
    checkout.save(update_fields=["shipping_method", "last_change"])


def is_fully_paid(
    checkout: Checkout, lines: Iterable[CheckoutLine], discounts: Iterable[DiscountInfo]
):
    """Check if provided payment methods cover the checkout's total amount.

    Note that these payments may not be captured or charged at all.
    """
    payments = [payment for payment in checkout.payments.all() if payment.is_active]
    total_paid = sum([p.total for p in payments])
    checkout_total = (
        calculations.checkout_total(checkout=checkout, lines=lines, discounts=discounts)
        - checkout.get_total_gift_cards_balance()
    )
    checkout_total = max(
        checkout_total, zero_taxed_money(checkout_total.currency)
    ).gross
    return total_paid >= checkout_total.amount


def clean_checkout(
    checkout: Checkout, lines: Iterable[CheckoutLine], discounts: Iterable[DiscountInfo]
):
    """Check if checkout can be completed."""
    if checkout.is_shipping_required():
        if not checkout.shipping_method:
            raise ValidationError(
                "Shipping method is not set",
                code=CheckoutErrorCode.SHIPPING_METHOD_NOT_SET.value,
            )
        if not checkout.shipping_address:
            raise ValidationError(
                "Shipping address is not set",
                code=CheckoutErrorCode.SHIPPING_ADDRESS_NOT_SET.value,
            )
        if not is_valid_shipping_method(checkout, lines, discounts):
            raise ValidationError(
                "Shipping method is not valid for your shipping address",
                code=CheckoutErrorCode.INVALID_SHIPPING_METHOD.value,
            )

    if not checkout.billing_address:
        raise ValidationError(
            "Billing address is not set",
            code=CheckoutErrorCode.BILLING_ADDRESS_NOT_SET.value,
        )

    if not is_fully_paid(checkout, lines, discounts):
        raise ValidationError(
            "Provided payment methods can not cover the checkout's total amount",
            code=CheckoutErrorCode.CHECKOUT_NOT_FULLY_PAID.value,
        )


def cancel_active_payments(checkout: Checkout):
    checkout.payments.filter(is_active=True).update(is_active=False)
