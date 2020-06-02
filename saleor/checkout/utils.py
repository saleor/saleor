"""Checkout-related utility functions."""
from datetime import date
from decimal import Decimal
from typing import Iterable, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max, Min, Sum
from django.utils import timezone
from django.utils.encoding import smart_text
from django.utils.translation import get_language
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ..account.models import User
from ..account.utils import store_user_address
from ..checkout import calculations
from ..checkout.error_codes import CheckoutErrorCode
from ..core.exceptions import ProductNotPublished
from ..core.taxes import quantize_price, zero_taxed_money
from ..core.utils.promo_code import (
    InvalidPromoCode,
    promo_code_is_gift_card,
    promo_code_is_voucher,
)
from ..discount import DiscountInfo, VoucherType
from ..discount.models import NotApplicable, Voucher
from ..discount.utils import (
    add_voucher_usage_by_customer,
    decrease_voucher_usage,
    get_discounted_lines,
    get_products_voucher_discount,
    increase_voucher_usage,
    remove_voucher_usage_by_customer,
    validate_voucher_for_checkout,
)
from ..giftcard.utils import (
    add_gift_card_code_to_checkout,
    remove_gift_card_code_from_checkout,
)
from ..order.actions import order_created
from ..order.emails import send_order_confirmation, send_staff_order_confirmation
from ..order.models import Order, OrderLine
from ..plugins.manager import get_plugins_manager
from ..shipping.models import ShippingMethod
from ..warehouse.availability import check_stock_quantity
from ..warehouse.management import allocate_stock
from . import AddressType
from .models import Checkout, CheckoutLine

COOKIE_NAME = "checkout"


def get_checkout_from_request(request, checkout_queryset=Checkout.objects.all()):
    """Fetch checkout from database or return a new instance based on cookie."""
    if request.user.is_authenticated:
        checkout, _ = get_user_checkout(request.user, checkout_queryset)
        user = request.user
    else:
        token = request.get_signed_cookie(COOKIE_NAME, default=None)
        checkout = get_anonymous_checkout_from_token(token, checkout_queryset)
        user = None
    if checkout is None:
        checkout = Checkout(user=user)
    checkout.set_country(request.country)
    return checkout


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


def get_anonymous_checkout_from_token(token, checkout_queryset=Checkout.objects.all()):
    """Return an open unassigned checkout with given token if any."""
    return checkout_queryset.filter(token=token, user=None).first()


def update_checkout_quantity(checkout):
    """Update the total quantity in checkout."""
    total_lines = checkout.lines.aggregate(total_quantity=Sum("quantity"))[
        "total_quantity"
    ]
    if not total_lines:
        total_lines = 0
    checkout.quantity = total_lines
    checkout.save(update_fields=["quantity"])

    manager = get_plugins_manager()
    manager.checkout_quantity_changed(checkout)


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


def _get_voucher_data_for_order(checkout: Checkout) -> dict:
    """Fetch, process and return voucher/discount data from checkout.

    Careful! It should be called inside a transaction.

    :raises NotApplicable: When the voucher is not applicable in the current checkout.
    """
    voucher = get_voucher_for_checkout(checkout, with_lock=True)

    if checkout.voucher_code and not voucher:
        msg = "Voucher expired in meantime. Order placement aborted."
        raise NotApplicable(msg)

    if not voucher:
        return {}

    increase_voucher_usage(voucher)
    if voucher.apply_once_per_customer:
        add_voucher_usage_by_customer(voucher, checkout.get_customer_email())
    return {
        "voucher": voucher,
        "discount": checkout.discount,
        "discount_name": checkout.discount_name,
        "translated_discount_name": checkout.translated_discount_name,
    }


def _process_shipping_data_for_order(
    checkout: Checkout, shipping_price: TaxedMoney
) -> dict:
    """Fetch, process and return shipping data from checkout."""
    if not checkout.is_shipping_required():
        return {}

    shipping_address = checkout.shipping_address

    if checkout.user:
        store_user_address(checkout.user, shipping_address, AddressType.SHIPPING)
        if (
            shipping_address
            and checkout.user.addresses.filter(pk=shipping_address.pk).exists()
        ):
            shipping_address = shipping_address.get_copy()

    return {
        "shipping_address": shipping_address,
        "shipping_method": checkout.shipping_method,
        "shipping_method_name": smart_text(checkout.shipping_method),
        "shipping_price": shipping_price,
        "weight": checkout.get_total_weight(),
    }


def _process_user_data_for_order(checkout: Checkout):
    """Fetch, process and return shipping data from checkout."""
    billing_address = checkout.billing_address

    if checkout.user:
        store_user_address(checkout.user, billing_address, AddressType.BILLING)
        if (
            billing_address
            and checkout.user.addresses.filter(pk=billing_address.pk).exists()
        ):
            billing_address = billing_address.get_copy()

    return {
        "user": checkout.user,
        "user_email": checkout.get_customer_email(),
        "billing_address": billing_address,
        "customer_note": checkout.note,
    }


def validate_gift_cards(checkout: Checkout):
    """Check if all gift cards assigned to checkout are available."""
    if (
        not checkout.gift_cards.count()
        == checkout.gift_cards.active(date=date.today()).count()
    ):
        msg = "Gift card has expired. Order placement cancelled."
        raise NotApplicable(msg)


def create_line_for_order(checkout_line: "CheckoutLine", discounts) -> OrderLine:
    """Create a line for the given order.

    :raises InsufficientStock: when there is not enough items in stock for this variant.
    """

    quantity = checkout_line.quantity
    variant = checkout_line.variant
    product = variant.product
    country = checkout_line.checkout.get_country()
    check_stock_quantity(variant, country, quantity)

    product_name = str(product)
    variant_name = str(variant)

    translated_product_name = str(product.translated)
    translated_variant_name = str(variant.translated)

    if translated_product_name == product_name:
        translated_product_name = ""

    if translated_variant_name == variant_name:
        translated_variant_name = ""

    manager = get_plugins_manager()
    total_line_price = manager.calculate_checkout_line_total(checkout_line, discounts)
    unit_price = quantize_price(
        total_line_price / checkout_line.quantity, total_line_price.currency
    )
    tax_rate = (
        unit_price.tax / unit_price.net
        if not isinstance(unit_price, Decimal)
        else Decimal("0.0")
    )
    line = OrderLine(
        product_name=product_name,
        variant_name=variant_name,
        translated_product_name=translated_product_name,
        translated_variant_name=translated_variant_name,
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,  # type: ignore
        tax_rate=tax_rate,
    )

    return line


def prepare_order_data(
    *, checkout: Checkout, lines: Iterable[CheckoutLine], tracking_code: str, discounts
) -> dict:
    """Run checks and return all the data from a given checkout to create an order.

    :raises NotApplicable InsufficientStock:
    """
    order_data = {}

    manager = get_plugins_manager()
    taxed_total = calculations.checkout_total(
        checkout=checkout, lines=lines, discounts=discounts
    )
    cards_total = checkout.get_total_gift_cards_balance()
    taxed_total.gross -= cards_total
    taxed_total.net -= cards_total

    taxed_total = max(taxed_total, zero_taxed_money(checkout.currency))

    shipping_total = manager.calculate_checkout_shipping(checkout, lines, discounts)
    order_data.update(_process_shipping_data_for_order(checkout, shipping_total))
    order_data.update(_process_user_data_for_order(checkout))
    order_data.update(
        {
            "language_code": get_language(),
            "tracking_client_id": tracking_code,
            "total": taxed_total,
        }
    )

    order_data["lines"] = [
        create_line_for_order(checkout_line=line, discounts=discounts)
        for line in checkout
    ]

    # validate checkout gift cards
    validate_gift_cards(checkout)

    # Get voucher data (last) as they require a transaction
    order_data.update(_get_voucher_data_for_order(checkout))

    # assign gift cards to the order

    order_data["total_price_left"] = (
        manager.calculate_checkout_subtotal(checkout, list(checkout), discounts)
        + shipping_total
        - checkout.discount
    ).gross

    manager.preprocess_order_creation(checkout, discounts)
    return order_data


def abort_order_data(order_data: dict):
    if "voucher" in order_data:
        voucher = order_data["voucher"]
        decrease_voucher_usage(voucher)
        if "user_email" in order_data:
            remove_voucher_usage_by_customer(voucher, order_data["user_email"])


@transaction.atomic
def create_order(
    *, checkout: Checkout, order_data: dict, user: User, redirect_url: str
) -> Order:
    """Create an order from the checkout.

    Each order will get a private copy of both the billing and the shipping
    address (if shipping).

    If any of the addresses is new and the user is logged in the address
    will also get saved to that user's address book.

    Current user's language is saved in the order so we can later determine
    which language to use when sending email.
    """
    from ..order.utils import add_gift_card_to_order

    order = Order.objects.filter(checkout_token=checkout.token).first()
    if order is not None:
        return order

    total_price_left = order_data.pop("total_price_left")
    order_lines = order_data.pop("lines")

    order = Order.objects.create(**order_data, checkout_token=checkout.token)
    order.lines.set(order_lines, bulk=False)

    # allocate stocks from the lines
    for line in order_lines:  # type: OrderLine
        variant = line.variant
        if variant and variant.track_inventory:
            allocate_stock(line, checkout.get_country(), line.quantity)

    # Add gift cards to the order
    for gift_card in checkout.gift_cards.select_for_update():
        total_price_left = add_gift_card_to_order(order, gift_card, total_price_left)

    # assign checkout payments to the order
    checkout.payments.update(order=order)

    # copy metadata from the checkout into the new order
    order.metadata = checkout.metadata
    order.private_metadata = checkout.private_metadata
    order.save()

    order_created(order=order, user=user)

    # Send the order confirmation email
    transaction.on_commit(
        lambda: send_order_confirmation.delay(order.pk, redirect_url, user.pk)
    )
    transaction.on_commit(
        lambda: send_staff_order_confirmation.delay(order.pk, redirect_url)
    )

    return order


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
