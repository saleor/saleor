"""Checkout-related utility functions."""
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple, Union, cast

import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone
from prices import Money

from ..account.models import User
from ..core.exceptions import ProductNotPublished
from ..core.taxes import zero_money, zero_taxed_money
from ..core.utils.promo_code import (
    InvalidPromoCode,
    promo_code_is_gift_card,
    promo_code_is_voucher,
)
from ..discount import DiscountInfo, VoucherType
from ..discount.interface import VoucherInfo, fetch_voucher_info
from ..discount.models import NotApplicable, Voucher
from ..discount.utils import (
    get_products_voucher_discount,
    validate_voucher_for_checkout,
)
from ..giftcard.utils import (
    add_gift_card_code_to_checkout,
    remove_gift_card_code_from_checkout,
)
from ..plugins.manager import PluginsManager
from ..product import models as product_models
from ..shipping.interface import ShippingMethodData
from ..shipping.models import ShippingMethod, ShippingMethodChannelListing
from ..shipping.utils import convert_to_shipping_method_data
from ..warehouse.availability import (
    check_stock_and_preorder_quantity,
    check_stock_and_preorder_quantity_bulk,
)
from ..warehouse.models import Warehouse
from ..warehouse.reservations import reserve_stocks_and_preorders
from . import AddressType, calculations
from .error_codes import CheckoutErrorCode
from .fetch import (
    update_checkout_info_delivery_method,
    update_checkout_info_shipping_address,
)
from .models import Checkout, CheckoutLine

if TYPE_CHECKING:
    # flake8: noqa
    from decimal import Decimal

    from prices import TaxedMoney

    from ..account.models import Address
    from ..order.models import Order
    from .fetch import CheckoutInfo, CheckoutLineInfo


PRIVATE_META_APP_SHIPPING_ID = "external_app_shipping_id"


def get_user_checkout(
    user: User, checkout_queryset=Checkout.objects.all()
) -> Tuple[Optional[Checkout], bool]:
    return checkout_queryset.filter(user=user, channel__is_active=True).first()


def check_variant_in_stock(
    checkout: Checkout,
    variant: product_models.ProductVariant,
    channel_slug: str,
    quantity: int = 1,
    replace: bool = False,
    check_quantity: bool = True,
    checkout_lines: Optional[List["CheckoutLine"]] = None,
    check_reservations: bool = False,
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
        check_stock_and_preorder_quantity(
            variant,
            checkout.get_country(),
            channel_slug,
            new_quantity,
            checkout_lines,
            check_reservations,
        )

    return new_quantity, line


def add_variant_to_checkout(
    checkout_info: "CheckoutInfo",
    variant: product_models.ProductVariant,
    quantity: int = 1,
    price_override: Optional["Decimal"] = None,
    replace: bool = False,
    check_quantity: bool = True,
):
    """Add a product variant to checkout.

    If `replace` is truthy then any previous quantity is discarded instead
    of added to.

    This function is not used outside of test suite.
    """
    checkout = checkout_info.checkout
    channel_slug = checkout_info.channel.slug

    product_channel_listing = product_models.ProductChannelListing.objects.filter(
        channel_id=checkout.channel_id, product_id=variant.product_id
    ).first()
    if not product_channel_listing or not product_channel_listing.is_published:
        raise ProductNotPublished()

    new_quantity, line = check_variant_in_stock(
        checkout,
        variant,
        channel_slug,
        quantity=quantity,
        replace=replace,
        check_quantity=check_quantity,
    )

    if line is None:
        line = checkout.lines.filter(variant=variant).first()

    if new_quantity == 0:
        if line is not None:
            line.delete()
            line = None
    elif line is None:
        line = checkout.lines.create(
            checkout=checkout,
            variant=variant,
            quantity=new_quantity,
            price_override=price_override,
        )
    elif new_quantity > 0:
        line.quantity = new_quantity
        line.save(update_fields=["quantity"])

    return checkout


def calculate_checkout_quantity(lines: Iterable["CheckoutLineInfo"]):
    return sum([line_info.line.quantity for line_info in lines])


def add_variants_to_checkout(
    checkout,
    variants,
    checkout_lines_data,
    channel_slug,
    replace=False,
    replace_reservations=False,
    reservation_length: Optional[int] = None,
):
    """Add variants to checkout.

    If a variant is not placed in checkout, a new checkout line will be created.
    If quantity is set to 0, checkout line will be deleted.
    Otherwise, quantity will be added or replaced (if replace argument is True).
    """
    country_code = checkout.get_country()

    checkout_lines = checkout.lines.select_related("variant")
    variant_ids_in_lines = {line.variant_id: line for line in checkout_lines}
    to_create: List[CheckoutLine] = []
    to_update: List[CheckoutLine] = []
    to_delete: List[CheckoutLine] = []
    for variant, line_data in zip(variants, checkout_lines_data):
        _append_line_to_update(
            to_update, to_delete, variant, line_data, replace, variant_ids_in_lines
        )
        _append_line_to_delete(to_delete, variant, line_data, variant_ids_in_lines)
        _append_line_to_create(
            to_create, checkout, variant, line_data, variant_ids_in_lines
        )
    if to_delete:
        CheckoutLine.objects.filter(pk__in=[line.pk for line in to_delete]).delete()
    if to_update:
        CheckoutLine.objects.bulk_update(to_update, ["quantity", "price_override"])
    if to_create:
        CheckoutLine.objects.bulk_create(to_create)

    to_reserve = to_create + to_update
    if reservation_length and to_reserve:
        updated_lines_ids = [line.pk for line in to_reserve + to_delete]
        for line in checkout_lines:
            if line.pk not in updated_lines_ids:
                to_reserve.append(line)
                variants.append(line.variant)

        reserve_stocks_and_preorders(
            to_reserve,
            variants,
            country_code,
            channel_slug,
            reservation_length,
            replace=replace_reservations,
        )

    return checkout


def _append_line_to_update(
    to_update, to_delete, variant, line_data, replace, variant_ids_in_lines
):
    if variant.pk not in variant_ids_in_lines:
        return
    line = variant_ids_in_lines[variant.pk]
    if line_data.quantity_to_update:
        quantity = line_data.quantity
        if quantity > 0:
            if replace:
                line.quantity = quantity
            else:
                line.quantity += quantity
            to_update.append(line)
    if line_data.custom_price_to_update:
        if line not in to_delete:
            line.price_override = line_data.custom_price
            to_update.append(line)


def _append_line_to_delete(to_delete, variant, line_data, variant_ids_in_lines):
    if variant.pk not in variant_ids_in_lines:
        return
    line = variant_ids_in_lines[variant.pk]
    quantity = line_data.quantity
    if line_data.quantity_to_update:
        if quantity <= 0:
            to_delete.append(line)


def _append_line_to_create(
    to_create, checkout, variant, line_data, variant_ids_in_lines
):
    if variant.pk not in variant_ids_in_lines:
        if line_data.quantity > 0:
            to_create.append(
                CheckoutLine(
                    checkout=checkout,
                    variant=variant,
                    quantity=line_data.quantity,
                    price_override=line_data.custom_price,
                )
            )


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


def change_shipping_address_in_checkout(
    checkout_info: "CheckoutInfo",
    address: "Address",
    lines: Iterable["CheckoutLineInfo"],
    discounts: Iterable[DiscountInfo],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"],
):
    """Save shipping address in checkout if changed.

    Remove previously saved address if not connected to any user.
    """
    checkout = checkout_info.checkout
    changed, remove = _check_new_checkout_address(
        checkout, address, AddressType.SHIPPING
    )
    if changed:
        if remove:
            checkout.shipping_address.delete()  # type: ignore
        checkout.shipping_address = address
        update_checkout_info_shipping_address(
            checkout_info, address, lines, discounts, manager, shipping_channel_listings
        )
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
    shipping_method = checkout_info.delivery_method_info.delivery_method
    if not shipping_method:
        msg = "Please select a delivery method first."
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
    lines: Iterable["CheckoutLineInfo"], voucher_info: "VoucherInfo"
) -> Iterable["CheckoutLineInfo"]:

    discounted_lines = []
    if (
        voucher_info.product_pks
        or voucher_info.collection_pks
        or voucher_info.category_pks
        or voucher_info.variant_pks
    ):
        for line_info in lines:
            line_variant = line_info.variant
            line_product = line_info.product
            line_category = line_info.product.category
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
    voucher_info = fetch_voucher_info(voucher)
    discounted_lines: Iterable["CheckoutLineInfo"] = get_discounted_lines(
        lines, voucher_info
    )
    address = checkout_info.shipping_address or checkout_info.billing_address
    discounts = discounts or []

    for line_info in discounted_lines:
        line = line_info.line
        line_unit_price = manager.calculate_checkout_line_unit_price(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
        ).price_with_sale.gross
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
        # The specific product voucher is propagated on specific line's prices
        return zero_money(checkout_info.checkout.currency)
    raise NotImplementedError("Unknown discount type")


def get_voucher_for_checkout(
    checkout: "Checkout",
    channel_slug: str,
    with_lock: bool = False,
    with_prefetch: bool = False,
) -> Optional[Voucher]:
    """Return voucher assigned to checkout."""
    if checkout.voucher_code is not None:
        vouchers = Voucher.objects
        vouchers = vouchers.active_in_channel(
            date=timezone.now(), channel_slug=channel_slug
        )
        if with_prefetch:
            vouchers.prefetch_related(
                "products", "collections", "categories", "variants", "channel_listings"
            )
        try:
            qs = vouchers
            voucher = qs.get(code=checkout.voucher_code)
            if voucher and voucher.usage_limit is not None and with_lock:
                voucher = vouchers.select_for_update().get(code=checkout.voucher_code)
            return voucher
        except Voucher.DoesNotExist:
            return None
    return None


def get_voucher_for_checkout_info(
    checkout_info: "CheckoutInfo", with_lock: bool = False, with_prefetch: bool = False
) -> Optional[Voucher]:
    """Return voucher with voucher code saved in checkout if active or None."""
    checkout = checkout_info.checkout
    return get_voucher_for_checkout(
        checkout,
        channel_slug=checkout_info.channel.slug,
        with_lock=with_lock,
        with_prefetch=with_prefetch,
    )


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
    if voucher := checkout_info.voucher:
        address = checkout_info.shipping_address or checkout_info.billing_address
        try:
            discount = get_voucher_discount_for_checkout(
                manager, voucher, checkout_info, lines, address, discounts
            )
        except NotApplicable:
            remove_voucher_from_checkout(checkout)
            checkout_info.voucher = None
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
                    "last_change",
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
        user_email = cast(str, checkout_info.get_customer_email())
        add_gift_card_code_to_checkout(
            checkout_info.checkout,
            user_email,
            promo_code,
            checkout_info.channel.currency_code,
        )
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
            "last_change",
        ]
    )
    checkout_info.voucher = voucher


def remove_promo_code_from_checkout(checkout_info: "CheckoutInfo", promo_code: str):
    """Remove gift card or voucher data from checkout."""
    if promo_code_is_voucher(promo_code):
        remove_voucher_code_from_checkout(checkout_info, promo_code)
    elif promo_code_is_gift_card(promo_code):
        remove_gift_card_code_from_checkout(checkout_info.checkout, promo_code)


def remove_voucher_code_from_checkout(checkout_info: "CheckoutInfo", voucher_code: str):
    """Remove voucher data from checkout by code."""
    existing_voucher = checkout_info.voucher
    if existing_voucher and existing_voucher.code == voucher_code:
        remove_voucher_from_checkout(checkout_info.checkout)
        checkout_info.voucher = None


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
            "last_change",
        ]
    )


def get_valid_internal_shipping_methods_for_checkout(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    subtotal: "TaxedMoney",
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"],
    country_code: Optional[str] = None,
) -> List[ShippingMethodData]:
    if not is_shipping_required(lines):
        return []
    if not checkout_info.shipping_address:
        return []

    shipping_methods = ShippingMethod.objects.applicable_shipping_methods_for_instance(
        checkout_info.checkout,
        channel_id=checkout_info.checkout.channel_id,
        price=subtotal.gross,
        country_code=country_code,
        lines=lines,
    )

    channel_listings_map = {
        listing.shipping_method_id: listing for listing in shipping_channel_listings
    }

    internal_methods = []
    for method in shipping_methods:
        listing = channel_listings_map.get(method.pk)
        shipping_method_data = convert_to_shipping_method_data(method, listing)
        if shipping_method_data:
            internal_methods.append(shipping_method_data)

    return internal_methods


def get_valid_collection_points_for_checkout(
    lines: Iterable["CheckoutLineInfo"],
    country_code: Optional[str] = None,
    quantity_check: bool = True,
):
    """Return a collection of `Warehouse`s that can be used as a collection point.

    Note that `quantity_check=False` should be used, when stocks quantity will
    be validated in further steps (checkout completion) in order to raise
    'InsufficientProductStock' error instead of 'InvalidShippingError'.
    """

    if not is_shipping_required(lines):
        return []
    if not country_code:
        return []
    line_ids = [line_info.line.id for line_info in lines]
    lines = CheckoutLine.objects.filter(id__in=line_ids)

    return (
        Warehouse.objects.applicable_for_click_and_collect(lines, country_code)
        if quantity_check
        else Warehouse.objects.applicable_for_click_and_collect_no_quantity_check(
            lines, country_code
        )
    )


def clear_delivery_method(checkout_info: "CheckoutInfo"):
    checkout = checkout_info.checkout
    checkout.collection_point = None
    checkout.shipping_method = None
    update_checkout_info_delivery_method(checkout_info, None)
    delete_external_shipping_id(checkout=checkout)
    checkout.save(
        update_fields=[
            "shipping_method",
            "collection_point",
            "private_metadata",
            "last_change",
        ]
    )


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


def validate_variants_in_checkout_lines(lines: Iterable["CheckoutLineInfo"]):
    variants_listings_map = {line.variant.id: line.channel_listing for line in lines}

    not_available_variants = [
        variant_id
        for variant_id, channel_listing in variants_listings_map.items()
        if channel_listing is None or channel_listing.price is None
    ]
    if not_available_variants:
        not_available_variants_ids = {
            graphene.Node.to_global_id("ProductVariant", pk)
            for pk in not_available_variants
        }
        error_code = CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines with unavailable variants.",
                    code=error_code,  # type: ignore
                    params={"variants": not_available_variants_ids},
                )
            }
        )


def set_external_shipping_id(checkout: Checkout, app_shipping_id: str):
    checkout.store_value_in_private_metadata(
        {PRIVATE_META_APP_SHIPPING_ID: app_shipping_id}
    )


def get_external_shipping_id(container: Union["Checkout", "Order"]):
    return container.get_value_from_private_metadata(PRIVATE_META_APP_SHIPPING_ID)


def delete_external_shipping_id(checkout: Checkout):
    checkout.delete_value_from_private_metadata(PRIVATE_META_APP_SHIPPING_ID)
