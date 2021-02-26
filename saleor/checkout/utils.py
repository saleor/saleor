"""Checkout-related utility functions."""
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from prices import Money

from ..account.models import User
from ..core.exceptions import ProductNotPublished
from ..core.taxes import zero_taxed_money
from ..core.utils.promo_code import (
    InvalidPromoCode,
    promo_code_is_gift_card,
    promo_code_is_voucher,
)
from ..discount import DiscountInfo, VoucherType
from ..discount.models import NotApplicable, Voucher
from ..discount.utils import (
    get_products_voucher_discount,
    validate_voucher_for_checkout,
)
from ..giftcard.utils import (
    add_gift_card_code_to_checkout,
    remove_gift_card_code_from_checkout,
)
from ..plugins.manager import PluginsManager, get_plugins_manager
from ..product import models as product_models
from ..shipping.models import ShippingMethod
from ..warehouse.availability import check_stock_quantity, check_stock_quantity_bulk
from . import AddressType, calculations
from .error_codes import CheckoutErrorCode
from .fetch import (
    update_checkout_info_shipping_address,
    update_checkout_info_shipping_method,
)
from .models import Checkout, CheckoutLine

if TYPE_CHECKING:
    # flake8: noqa
    from prices import TaxedMoney

    from ..account.models import Address
    from .fetch import CheckoutInfo, CheckoutLineInfo


def get_user_checkout(
    user: User, checkout_queryset=Checkout.objects.all()
) -> Tuple[Optional[Checkout], bool]:
    return checkout_queryset.filter(user=user, channel__is_active=True).first()


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
    product_channel_listing = variant.product.channel_listings.filter(
        channel_id=checkout.channel_id
    ).first()
    if not product_channel_listing or not product_channel_listing.is_published:
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

    checkout = update_checkout_quantity(checkout)
    return checkout


def add_variants_to_checkout(checkout, variants, quantities):
    """Add variants to checkout.

    Suitable for new checkouts as it always creates new checkout lines without checking
    if there are any existing ones already.
    """

    # check quantities
    country_code = checkout.get_country()
    check_stock_quantity_bulk(variants, country_code, quantities)

    channel_listings = product_models.ProductChannelListing.objects.filter(
        channel_id=checkout.channel.id,
        product_id__in=[v.product_id for v in variants],
    )
    channel_listings_by_product_id = {cl.product_id: cl for cl in channel_listings}

    # check if variants are published
    for variant in variants:
        product_channel_listing = channel_listings_by_product_id[variant.product_id]
        if not product_channel_listing or not product_channel_listing.is_published:
            raise ProductNotPublished()

    # create checkout lines
    lines = []
    for variant, quantity in zip(variants, quantities):
        lines.append(
            CheckoutLine(checkout=checkout, variant=variant, quantity=quantity)
        )
    checkout.lines.bulk_create(lines)
    checkout = update_checkout_quantity(checkout)
    return checkout


def update_checkout_quantity(checkout):
    """Update the total quantity in checkout."""
    total_lines = checkout.lines.aggregate(total_quantity=Sum("quantity"))[
        "total_quantity"
    ]
    if not total_lines:
        total_lines = 0
    checkout.quantity = total_lines
    checkout.save(update_fields=["quantity"])
    return checkout


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


def change_shipping_address_in_checkout(checkout_info, address, lines, discounts):
    """Save shipping address in checkout if changed.

    Remove previously saved address if not connected to any user.
    """
    checkout = checkout_info.checkout
    changed, remove = _check_new_checkout_address(
        checkout, address, AddressType.SHIPPING
    )
    if changed:
        if remove:
            checkout.shipping_address.delete()
        checkout.shipping_address = address
        update_checkout_info_shipping_address(checkout_info, address, lines, discounts)
        checkout.save(update_fields=["shipping_address", "last_change"])


def _get_shipping_voucher_discount_for_checkout(
    manager: PluginsManager,
    voucher: Voucher,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    """Calculate discount value for a voucher of shipping type."""
    if not is_shipping_required(lines):
        msg = "Your order does not require shipping."
        raise NotApplicable(msg)
    shipping_method = checkout_info.shipping_method
    if not shipping_method:
        msg = "Please select a shipping method first."
        raise NotApplicable(msg)

    # check if voucher is limited to specified countries
    if address:
        if voucher.countries and address.country.code not in voucher.countries:
            msg = "This offer is not valid in your country."
            raise NotApplicable(msg)

    shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    ).gross
    return voucher.get_discount_amount_for(shipping_price, checkout_info.channel)


def _get_products_voucher_discount(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    voucher,
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    """Calculate products discount value for a voucher, depending on its type."""
    prices = None
    if voucher.type == VoucherType.SPECIFIC_PRODUCT:
        prices = get_prices_of_discounted_specific_product(
            manager, checkout_info, lines, voucher, discounts
        )
    if not prices:
        msg = "This offer is only valid for selected items."
        raise NotApplicable(msg)
    return get_products_voucher_discount(voucher, prices, checkout_info.channel)


def get_discounted_lines(
    lines: Iterable["CheckoutLineInfo"], voucher
) -> Iterable["CheckoutLineInfo"]:
    discounted_products = voucher.products.all()
    discounted_categories = set(voucher.categories.all())
    discounted_collections = set(voucher.collections.all())

    discounted_lines = []
    if discounted_products or discounted_collections or discounted_categories:
        for line_info in lines:
            line_product = line_info.product
            line_category = line_info.product.category
            line_collections = set(line_info.collections)
            if line_info.variant and (
                line_product in discounted_products
                or line_category in discounted_categories
                or line_collections.intersection(discounted_collections)
            ):
                discounted_lines.append(line_info)
    else:
        # If there's no discounted products, collections or categories,
        # it means that all products are discounted
        discounted_lines.extend(lines)
    return discounted_lines


def get_prices_of_discounted_specific_product(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    voucher: Voucher,
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> List[Money]:
    """Get prices of variants belonging to the discounted specific products.

    Specific products are products, collections and categories.
    Product must be assigned directly to the discounted category, assigning
    product to child category won't work.
    """
    line_prices = []
    discounted_lines: Iterable["CheckoutLineInfo"] = get_discounted_lines(
        lines, voucher
    )
    address = checkout_info.shipping_address or checkout_info.billing_address
    discounts = discounts or []

    for line_info in discounted_lines:
        line = line_info.line
        line_total = calculations.checkout_line_total(
            manager=manager,
            checkout_info=checkout_info,
            checkout_line_info=line_info,
            discounts=discounts,
        ).gross
        line_unit_price = manager.calculate_checkout_line_unit_price(
            line_total,
            line.quantity,
            checkout_info.checkout,
            line_info,
            address,
            discounts,
            checkout_info.channel,
        )
        line_prices.extend([line_unit_price] * line.quantity)

    return line_prices


def get_voucher_discount_for_checkout(
    manager: PluginsManager,
    voucher: Voucher,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> Money:
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    validate_voucher_for_checkout(manager, voucher, checkout_info, lines, discounts)
    if voucher.type == VoucherType.ENTIRE_ORDER:
        subtotal = calculations.checkout_subtotal(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=address,
            discounts=discounts,
        ).gross
        return voucher.get_discount_amount_for(subtotal, checkout_info.channel)
    if voucher.type == VoucherType.SHIPPING:
        return _get_shipping_voucher_discount_for_checkout(
            manager, voucher, checkout_info, lines, address, discounts
        )
    if voucher.type == VoucherType.SPECIFIC_PRODUCT:
        return _get_products_voucher_discount(
            manager, checkout_info, lines, voucher, discounts
        )
    raise NotImplementedError("Unknown discount type")


def get_voucher_for_checkout(
    checkout_info: "CheckoutInfo", vouchers=None, with_lock: bool = False
) -> Optional[Voucher]:
    """Return voucher with voucher code saved in checkout if active or None."""
    checkout = checkout_info.checkout
    if checkout.voucher_code is not None:
        if vouchers is None:
            vouchers = Voucher.objects.active_in_channel(
                date=timezone.now(), channel_slug=checkout_info.channel.slug
            )
        try:
            qs = vouchers
            if with_lock:
                qs = vouchers.select_for_update()
            return qs.get(code=checkout.voucher_code)
        except Voucher.DoesNotExist:
            return None
    return None


def recalculate_checkout_discount(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    discounts: Iterable[DiscountInfo],
):
    """Recalculate `checkout.discount` based on the voucher.

    Will clear both voucher and discount if the discount is no longer
    applicable.
    """
    checkout = checkout_info.checkout
    voucher = get_voucher_for_checkout(checkout_info)
    if voucher is not None:
        address = checkout_info.shipping_address or checkout_info.billing_address
        try:
            discount = get_voucher_discount_for_checkout(
                manager, voucher, checkout_info, lines, address, discounts
            )
        except NotApplicable:
            remove_voucher_from_checkout(checkout)
        else:
            subtotal = calculations.checkout_subtotal(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                discounts=discounts,
            ).gross
            checkout.discount = (
                min(discount, subtotal)
                if voucher.type != VoucherType.SHIPPING
                else discount
            )
            checkout.discount_name = voucher.name
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
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    promo_code: str,
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    """Add gift card or voucher data to checkout.

    Raise InvalidPromoCode if promo code does not match to any voucher or gift card.
    """
    if promo_code_is_voucher(promo_code):
        add_voucher_code_to_checkout(
            manager, checkout_info, lines, promo_code, discounts
        )
    elif promo_code_is_gift_card(promo_code):
        add_gift_card_code_to_checkout(checkout_info.checkout, promo_code)
    else:
        raise InvalidPromoCode()


def add_voucher_code_to_checkout(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    voucher_code: str,
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    """Add voucher data to checkout by code.

    Raise InvalidPromoCode() if voucher of given type cannot be applied.
    """
    try:
        voucher = Voucher.objects.active_in_channel(
            date=timezone.now(), channel_slug=checkout_info.channel.slug
        ).get(code=voucher_code)
    except Voucher.DoesNotExist:
        raise InvalidPromoCode()
    try:
        add_voucher_to_checkout(manager, checkout_info, lines, voucher, discounts)
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
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    voucher: Voucher,
    discounts: Optional[Iterable[DiscountInfo]] = None,
):
    """Add voucher data to checkout.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    checkout = checkout_info.checkout
    address = checkout_info.shipping_address or checkout_info.billing_address
    discount = get_voucher_discount_for_checkout(
        manager, voucher, checkout_info, lines, address, discounts
    )
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


def remove_promo_code_from_checkout(checkout_info: "CheckoutInfo", promo_code: str):
    """Remove gift card or voucher data from checkout."""
    if promo_code_is_voucher(promo_code):
        remove_voucher_code_from_checkout(checkout_info, promo_code)
    elif promo_code_is_gift_card(promo_code):
        remove_gift_card_code_from_checkout(checkout_info.checkout, promo_code)


def remove_voucher_code_from_checkout(checkout_info: "CheckoutInfo", voucher_code: str):
    """Remove voucher data from checkout by code."""
    existing_voucher = get_voucher_for_checkout(checkout_info)
    if existing_voucher and existing_voucher.code == voucher_code:
        remove_voucher_from_checkout(checkout_info.checkout)


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
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    discounts: Iterable[DiscountInfo],
    country_code: Optional[str] = None,
    subtotal: Optional["TaxedMoney"] = None,
):
    if not is_shipping_required(lines):
        return None
    if not checkout_info.shipping_address:
        return None
    # TODO: subtotal should comes from arg instead of calculate it in this function
    # use info.context.plugins from resolver
    if subtotal is None:
        manager = get_plugins_manager()
        subtotal = manager.calculate_checkout_subtotal(
            checkout_info, lines, checkout_info.shipping_address, discounts
        )
    return ShippingMethod.objects.applicable_shipping_methods_for_instance(
        checkout_info.checkout,
        channel_id=checkout_info.checkout.channel_id,
        price=subtotal.gross,
        country_code=country_code,
        lines=lines,
    )


def is_valid_shipping_method(checkout_info: "CheckoutInfo"):
    """Check if shipping method is valid and remove (if not)."""
    if not checkout_info.shipping_method:
        return False
    if not checkout_info.shipping_address:
        return False

    valid_methods = checkout_info.valid_shipping_methods
    if valid_methods is None or checkout_info.shipping_method not in valid_methods:
        clear_shipping_method(checkout_info)
        return False
    return True


def clear_shipping_method(checkout_info: "CheckoutInfo"):
    checkout = checkout_info.checkout
    checkout.shipping_method = None
    update_checkout_info_shipping_method(checkout_info, None)
    checkout.save(update_fields=["shipping_method", "last_change"])


def is_fully_paid(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    discounts: Iterable[DiscountInfo],
):
    """Check if provided payment methods cover the checkout's total amount.

    Note that these payments may not be captured or charged at all.
    """
    checkout = checkout_info.checkout
    payments = [payment for payment in checkout.payments.all() if payment.is_active]
    total_paid = sum([p.total for p in payments])
    address = checkout_info.shipping_address or checkout_info.billing_address
    checkout_total = (
        calculations.checkout_total(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=address,
            discounts=discounts,
        )
        - checkout.get_total_gift_cards_balance()
    )
    checkout_total = max(
        checkout_total, zero_taxed_money(checkout_total.currency)
    ).gross
    return total_paid >= checkout_total.amount


def cancel_active_payments(checkout: Checkout):
    checkout.payments.filter(is_active=True).update(is_active=False)


def is_shipping_required(lines: Iterable["CheckoutLineInfo"]):
    """Check if shipping is required for given checkout lines."""
    return any(
        line_info.product.product_type.is_shipping_required for line_info in lines
    )
