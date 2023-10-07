"""Checkout-related utility functions."""
from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple, Union, cast

import graphene
from django.core.exceptions import ValidationError
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
from ..core.utils.translations import get_translation
from ..discount import VoucherType
from ..discount.interface import VoucherInfo, fetch_voucher_info
from ..discount.models import NotApplicable, Voucher
from ..discount.utils import (
    generate_sale_discount_objects_for_checkout,
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
from ..warehouse.availability import check_stock_and_preorder_quantity
from ..warehouse.models import Warehouse
from ..warehouse.reservations import reserve_stocks_and_preorders
from . import AddressType, base_calculations, calculations
from .error_codes import CheckoutErrorCode
from .fetch import (
    update_checkout_info_delivery_method,
    update_checkout_info_shipping_address,
)
from .models import Checkout, CheckoutLine, CheckoutMetadata

if TYPE_CHECKING:
    from ..account.models import Address
    from ..order.models import Order
    from .fetch import CheckoutInfo, CheckoutLineInfo


PRIVATE_META_APP_SHIPPING_ID = "external_app_shipping_id"


def invalidate_checkout_prices(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    manager: "PluginsManager",
    *,
    recalculate_discount: bool = True,
    save: bool,
) -> List[str]:
    """Mark checkout as ready for prices recalculation."""
    checkout = checkout_info.checkout

    if recalculate_discount:
        generate_sale_discount_objects_for_checkout(checkout_info, lines)
        recalculate_checkout_discount(manager, checkout_info, lines)

    checkout.price_expiration = timezone.now()
    updated_fields = ["price_expiration", "last_change"]

    if save:
        checkout.save(update_fields=updated_fields)

    return updated_fields


def get_user_checkout(
    user: User, checkout_queryset=Checkout.objects.all()
) -> Optional[Checkout]:
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
    force_new_line: bool = False,
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

    if force_new_line:
        checkout.lines.create(
            variant=variant,
            quantity=quantity,
            price_override=price_override,
        )
        return checkout

    if line is None:
        line = checkout.lines.filter(variant=variant).first()

    if new_quantity == 0:
        if line is not None:
            line.delete()
    elif line is None:
        checkout.lines.create(
            variant=variant,
            quantity=new_quantity,
            currency=checkout.currency,
            price_override=price_override,
        )
    elif new_quantity > 0:
        line.quantity = new_quantity
        line.save(update_fields=["quantity"])

    # invalidate calculated prices
    checkout.price_expiration = timezone.now()
    return checkout


def calculate_checkout_quantity(lines: Iterable["CheckoutLineInfo"]):
    return sum([line_info.line.quantity for line_info in lines])


def add_variants_to_checkout(
    checkout,
    variants,
    checkout_lines_data,
    channel,
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

    lines_by_id = {str(line.pk): line for line in checkout_lines}
    variants_map = {str(variant.pk): variant for variant in variants}

    to_create: List[CheckoutLine] = []
    to_update: List[CheckoutLine] = []
    to_delete: List[CheckoutLine] = []

    for line_data in checkout_lines_data:
        line = lines_by_id.get(line_data.line_id) if line_data.line_id else None
        if line:
            _append_line_to_update(to_update, to_delete, line_data, replace, line)
            _append_line_to_delete(to_delete, line_data, line)
        else:
            variant = variants_map[line_data.variant_id]
            _append_line_to_create(to_create, checkout, variant, line_data, line)

    if to_delete:
        CheckoutLine.objects.filter(pk__in=[line.pk for line in to_delete]).delete()
    if to_update:
        CheckoutLine.objects.bulk_update(
            to_update, ["quantity", "price_override", "metadata"]
        )
    if to_create:
        CheckoutLine.objects.bulk_create(to_create)

    to_reserve = to_create + to_update

    if reservation_length and to_reserve:
        updated_lines_ids = [line.pk for line in to_reserve + to_delete]

        # Validation for stock reservation should be performed on new and updated lines.
        # For already existing lines only reserved_until should be updated.
        lines_to_update_reservation_time = []
        for line in checkout_lines:
            if line.pk not in updated_lines_ids:
                lines_to_update_reservation_time.append(line)

        reserve_stocks_and_preorders(
            to_reserve,
            lines_to_update_reservation_time,
            variants,
            country_code,
            channel,
            reservation_length,
            replace=replace_reservations,
        )

    return checkout


def _get_line_if_exist(line_data, lines_by_ids):
    if line_data.line_id and line_data.line_id in lines_by_ids:
        return lines_by_ids[line_data.line_id]


def _append_line_to_update(to_update, to_delete, line_data, replace, line):
    if line_data.metadata_list:
        line.store_value_in_metadata(
            {data.key: data.value for data in line_data.metadata_list}
        )
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


def _append_line_to_delete(to_delete, line_data, line):
    quantity = line_data.quantity
    if line_data.quantity_to_update:
        if quantity <= 0:
            to_delete.append(line)


def _append_line_to_create(to_create, checkout, variant, line_data, line):
    if line is None:
        if line_data.quantity > 0:
            checkout_line = CheckoutLine(
                checkout=checkout,
                variant=variant,
                quantity=line_data.quantity,
                currency=checkout.currency,
                price_override=line_data.custom_price,
            )
            if line_data.metadata_list:
                checkout_line.store_value_in_metadata(
                    {data.key: data.value for data in line_data.metadata_list}
                )
            to_create.append(checkout_line)


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


def change_billing_address_in_checkout(checkout, address) -> List[str]:
    """Save billing address in checkout if changed.

    Remove previously saved address if not connected to any user.
    This function does not save anything to database and
    instead returns updated fields.
    """
    changed, remove = _check_new_checkout_address(
        checkout, address, AddressType.BILLING
    )
    updated_fields = []
    if changed:
        if remove:
            checkout.billing_address.delete()
        checkout.billing_address = address
        updated_fields = ["billing_address", "last_change"]
    return updated_fields


def change_shipping_address_in_checkout(
    checkout_info: "CheckoutInfo",
    address: "Address",
    lines: Iterable["CheckoutLineInfo"],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"],
):
    """Save shipping address in checkout if changed.

    Remove previously saved address if not connected to any user.
    This function does not save anything to database and
    instead returns updated fields.
    """
    checkout = checkout_info.checkout
    changed, remove = _check_new_checkout_address(
        checkout, address, AddressType.SHIPPING
    )
    updated_fields = []
    if changed:
        if remove and checkout.shipping_address:
            checkout.shipping_address.delete()
        checkout.shipping_address = address
        update_checkout_info_shipping_address(
            checkout_info, address, lines, manager, shipping_channel_listings
        )
        updated_fields = ["shipping_address", "last_change"]
    return updated_fields


def _get_shipping_voucher_discount_for_checkout(
    voucher: Voucher,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
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

    shipping_price = base_calculations.base_checkout_undiscounted_delivery_price(
        checkout_info=checkout_info, lines=lines
    )
    return voucher.get_discount_amount_for(shipping_price, checkout_info.channel)


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
) -> List[Money]:
    """Get prices of variants belonging to the discounted specific products.

    Specific products are products, collections and categories.
    Product must be assigned directly to the discounted category, assigning
    product to child category won't work.
    """
    voucher_info = fetch_voucher_info(voucher)
    discounted_lines: Iterable["CheckoutLineInfo"] = get_discounted_lines(
        lines, voucher_info
    )
    line_prices = get_base_lines_prices(checkout_info, discounted_lines)

    return line_prices


def get_base_lines_prices(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
):
    """Get base total price of checkout lines without voucher discount applied."""
    line_prices = []
    for line_info in lines:
        line = line_info.line
        line_unit_price = line.variant.get_price(
            line_info.product,
            line_info.collections,
            checkout_info.channel,
            line_info.channel_listing,
            [],
            line_info.line.price_override,
        )
        line_price = line_unit_price * line.quantity
        for discount in line_info.discounts:
            line_price -= Money(discount.amount_value, line_price.currency)
        line_unit_price = line_price / line.quantity
        line_prices.extend([line_unit_price] * line.quantity)
    return line_prices


def get_voucher_discount_for_checkout(
    manager: PluginsManager,
    voucher: Voucher,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
) -> Money:
    """Calculate discount value depending on voucher and discount types.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    validate_voucher_for_checkout(manager, voucher, checkout_info, lines)
    if voucher.type == VoucherType.ENTIRE_ORDER:
        if voucher.apply_once_per_order:
            prices = get_base_lines_prices(checkout_info, lines)
            return voucher.get_discount_amount_for(min(prices), checkout_info.channel)
        subtotal = base_calculations.base_checkout_subtotal(
            lines,
            checkout_info.channel,
            checkout_info.checkout.currency,
        )
        return voucher.get_discount_amount_for(subtotal, checkout_info.channel)
    if voucher.type == VoucherType.SHIPPING:
        return _get_shipping_voucher_discount_for_checkout(
            voucher,
            checkout_info,
            lines,
            address,
        )
    if voucher.type == VoucherType.SPECIFIC_PRODUCT:
        return _get_products_voucher_discount(manager, checkout_info, lines, voucher)
    raise NotImplementedError("Unknown discount type")


def _get_products_voucher_discount(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    voucher,
):
    """Calculate products discount value for a voucher, depending on its type."""
    prices = None
    if voucher.type == VoucherType.SPECIFIC_PRODUCT:
        prices = get_prices_of_discounted_specific_product(
            manager, checkout_info, lines, voucher
        )
    if not prices:
        msg = "This offer is only valid for selected items."
        raise NotApplicable(msg)
    return get_products_voucher_discount(voucher, prices, checkout_info.channel)


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


def check_voucher_for_checkout(
    voucher: Voucher,
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
):
    checkout = checkout_info.checkout
    address = checkout_info.shipping_address or checkout_info.billing_address
    try:
        discount = get_voucher_discount_for_checkout(
            manager,
            voucher,
            checkout_info,
            lines,
            address,
        )
        return discount
    except NotApplicable:
        remove_voucher_from_checkout(checkout)
        checkout_info.voucher = None
        return None


def recalculate_checkout_discount(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
):
    """Recalculate `checkout.discount` based on the voucher.

    Will clear both voucher and discount if the discount is no longer
    applicable.
    """
    checkout = checkout_info.checkout
    if voucher := checkout_info.voucher:
        discount = check_voucher_for_checkout(
            voucher,
            manager,
            checkout_info,
            lines,
        )
        if discount:
            subtotal = base_calculations.base_checkout_subtotal(
                lines,
                checkout_info.channel,
                checkout_info.checkout.currency,
            )
            checkout.discount = (
                min(discount, subtotal)
                if voucher.type != VoucherType.SHIPPING
                else discount
            )
            checkout.discount_name = voucher.name

            language_code = checkout.language_code
            translated_discount_name = get_translation(voucher, language_code).name
            checkout.translated_discount_name = (
                translated_discount_name
                if translated_discount_name != voucher.name
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
):
    """Add gift card or voucher data to checkout.

    Raise InvalidPromoCode if promo code does not match to any voucher or gift card.
    """
    if promo_code_is_voucher(promo_code):
        add_voucher_code_to_checkout(
            manager,
            checkout_info,
            lines,
            promo_code,
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
        add_voucher_to_checkout(
            manager,
            checkout_info,
            lines,
            voucher,
        )
    except NotApplicable:
        raise ValidationError(
            {
                "promo_code": ValidationError(
                    "Voucher is not applicable to this checkout.",
                    code=CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.value,
                )
            }
        )


def add_voucher_to_checkout(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    voucher: Voucher,
):
    """Add voucher data to checkout.

    Raise NotApplicable if voucher of given type cannot be applied.
    """
    checkout = checkout_info.checkout
    address = checkout_info.shipping_address or checkout_info.billing_address
    discount = get_voucher_discount_for_checkout(
        manager,
        voucher,
        checkout_info,
        lines,
        address,
    )
    checkout.voucher_code = voucher.code
    checkout.discount_name = voucher.name

    language_code = checkout.language_code
    translated_discount_name = get_translation(voucher, language_code).name
    checkout.translated_discount_name = (
        translated_discount_name if translated_discount_name != voucher.name else ""
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


def remove_promo_code_from_checkout(
    checkout_info: "CheckoutInfo", promo_code: str
) -> bool:
    """Remove gift card or voucher data from checkout.

    Return information whether promo code was removed.
    """
    if promo_code_is_voucher(promo_code):
        return remove_voucher_code_from_checkout(checkout_info, promo_code)
    elif promo_code_is_gift_card(promo_code):
        return remove_gift_card_code_from_checkout(checkout_info.checkout, promo_code)
    return False


def remove_voucher_code_from_checkout(
    checkout_info: "CheckoutInfo", voucher_code: str
) -> bool:
    """Remove voucher data from checkout by code.

    Return information whether promo code was removed.
    """
    existing_voucher = checkout_info.voucher
    if existing_voucher and existing_voucher.code == voucher_code:
        remove_voucher_from_checkout(checkout_info.checkout)
        checkout_info.voucher = None
        return True
    return False


def remove_voucher_from_checkout(checkout: Checkout):
    """Remove voucher data from checkout."""
    checkout.voucher_code = None
    checkout.discount_name = None
    checkout.translated_discount_name = None
    checkout.discount_amount = Decimal("0")
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
    subtotal: "Money",
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
        price=subtotal,
        country_code=country_code,
        lines=lines,
    )

    channel_listings_map = {
        listing.shipping_method_id: listing for listing in shipping_channel_listings
    }

    internal_methods: List[ShippingMethodData] = []
    for method in shipping_methods:
        listing = channel_listings_map.get(method.pk)
        if listing:
            shipping_method_data = convert_to_shipping_method_data(method, listing)
            internal_methods.append(shipping_method_data)

    return internal_methods


def get_valid_collection_points_for_checkout(
    lines: Iterable["CheckoutLineInfo"],
    channel_id: int,
    quantity_check: bool = True,
):
    """Return a collection of `Warehouse`s that can be used as a collection point.

    Note that `quantity_check=False` should be used, when stocks quantity will
    be validated in further steps (checkout completion) in order to raise
    'InsufficientProductStock' error instead of 'InvalidShippingError'.
    """
    if not is_shipping_required(lines):
        return []

    line_ids = [line_info.line.id for line_info in lines]
    lines = CheckoutLine.objects.filter(id__in=line_ids)

    return (
        Warehouse.objects.applicable_for_click_and_collect(lines, channel_id)
        if quantity_check
        else Warehouse.objects.applicable_for_click_and_collect_no_quantity_check(
            lines, channel_id
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
            "last_change",
        ]
    )
    get_checkout_metadata(checkout).save()


def is_fully_paid(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
):
    """Check if provided payment methods cover the checkout's total amount.

    Note that these payments may not be captured or charged at all.
    """
    checkout = checkout_info.checkout
    payments = [payment for payment in checkout.payments.all() if payment.is_active]
    total_paid = sum([p.total for p in payments])
    address = checkout_info.shipping_address or checkout_info.billing_address
    checkout_total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
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
        error_code = CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.value
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines with unavailable variants.",
                    code=error_code,
                    params={"variants": not_available_variants_ids},
                )
            }
        )


def set_external_shipping_id(checkout: Checkout, app_shipping_id: str):
    metadata = get_or_create_checkout_metadata(checkout)
    metadata.store_value_in_private_metadata(
        {PRIVATE_META_APP_SHIPPING_ID: app_shipping_id}
    )


def get_external_shipping_id(container: Union["Checkout", "Order"]):
    if type(container) == Checkout:
        container = get_checkout_metadata(container)
    return container.get_value_from_private_metadata(  # type:ignore
        PRIVATE_META_APP_SHIPPING_ID
    )


def delete_external_shipping_id(checkout: Checkout):
    metadata = get_or_create_checkout_metadata(checkout)
    metadata.delete_value_from_private_metadata(PRIVATE_META_APP_SHIPPING_ID)


def get_or_create_checkout_metadata(checkout: "Checkout") -> CheckoutMetadata:
    if hasattr(checkout, "metadata_storage"):
        return checkout.metadata_storage
    else:
        return CheckoutMetadata.objects.create(checkout=checkout)


def get_checkout_metadata(checkout: "Checkout"):
    if hasattr(checkout, "metadata_storage"):
        return checkout.metadata_storage
    else:
        return CheckoutMetadata(checkout=checkout)
