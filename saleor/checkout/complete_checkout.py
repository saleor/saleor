from datetime import date
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Tuple

from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.encoding import smart_text
from django.utils.translation import get_language
from prices import TaxedMoney

from ..account.error_codes import AccountErrorCode
from ..account.models import User
from ..account.utils import store_user_address
from ..checkout import calculations
from ..checkout.error_codes import CheckoutErrorCode
from ..core.exceptions import InsufficientStock
from ..core.taxes import TaxError, zero_taxed_money
from ..core.utils.url import validate_storefront_url
from ..discount import DiscountInfo
from ..discount.models import NotApplicable
from ..discount.utils import (
    add_voucher_usage_by_customer,
    decrease_voucher_usage,
    increase_voucher_usage,
    remove_voucher_usage_by_customer,
)
from ..order import OrderStatus
from ..order.actions import order_created
from ..order.emails import send_order_confirmation, send_staff_order_confirmation
from ..order.models import Order, OrderLine
from ..payment import PaymentError, gateway
from ..payment.models import Payment, Transaction
from ..payment.utils import store_customer_id
from ..product.models import ProductTranslation, ProductVariantTranslation
from ..warehouse.availability import check_stock_quantity_bulk
from ..warehouse.management import allocate_stock
from . import AddressType, models
from .checkout_cleaner import clean_checkout_payment, clean_checkout_shipping
from .models import Checkout
from .utils import get_voucher_for_checkout

if TYPE_CHECKING:
    from ..channel.models import Channel
    from ..checkout import CheckoutLineInfo
    from ..plugins.manager import PluginsManager


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
    checkout: Checkout,
    shipping_price: TaxedMoney,
    manager: "PluginsManager",
    lines: Iterable["CheckoutLineInfo"],
) -> dict:
    """Fetch, process and return shipping data from checkout."""
    shipping_address = checkout.shipping_address

    if checkout.user:
        store_user_address(
            checkout.user, shipping_address, AddressType.SHIPPING, manager=manager
        )
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
        "weight": checkout.get_total_weight(lines),
    }


def _process_user_data_for_order(checkout: Checkout, manager):
    """Fetch, process and return shipping data from checkout."""
    billing_address = checkout.billing_address

    if checkout.user:
        store_user_address(
            checkout.user, billing_address, AddressType.BILLING, manager=manager
        )
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


def _validate_gift_cards(checkout: Checkout):
    """Check if all gift cards assigned to checkout are available."""
    if (
        not checkout.gift_cards.count()
        == checkout.gift_cards.active(date=date.today()).count()
    ):
        msg = "Gift card has expired. Order placement cancelled."
        raise NotApplicable(msg)


def _create_line_for_order(
    manager: "PluginsManager",
    checkout: "Checkout",
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable[DiscountInfo],
    channel: "Channel",
    products_translation: Dict[int, Optional[str]],
    variants_translation: Dict[int, Optional[str]],
) -> OrderLine:
    """Create a line for the given order.

    :raises InsufficientStock: when there is not enough items in stock for this variant.
    """
    checkout_line = checkout_line_info.line
    quantity = checkout_line.quantity
    variant = checkout_line_info.variant
    channel_listing = checkout_line_info.channel_listing
    product = checkout_line_info.product
    collections = checkout_line_info.collections
    address = (
        checkout.shipping_address or checkout.billing_address
    )  # FIXME: check which address we need here

    product_name = str(product)
    variant_name = str(variant)

    translated_product_name = products_translation.get(product.id, "")
    translated_variant_name = variants_translation.get(variant.id, "")

    if translated_product_name == product_name:
        translated_product_name = ""

    if translated_variant_name == variant_name:
        translated_variant_name = ""

    total_line_price = manager.calculate_checkout_line_total(
        checkout,
        checkout_line,
        variant,
        product,
        collections,
        address,
        channel,
        channel_listing,
        discounts,
    )
    unit_price = manager.calculate_checkout_line_unit_price(total_line_price, quantity)
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout, checkout_line_info, address, discounts, unit_price
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
        total_price=total_line_price,
        tax_rate=tax_rate,
    )

    return line


def _create_lines_for_order(
    manager: "PluginsManager",
    checkout: "Checkout",
    lines: Iterable["CheckoutLineInfo"],
    discounts: Iterable[DiscountInfo],
    channel: "Channel",
) -> Iterable[OrderLine]:
    """Create a lines for the given order.

    :raises InsufficientStock: when there is not enough items in stock for this variant.
    """
    translation_language_code = get_language()
    country_code = checkout.get_country()
    variants = []
    quantities = []
    products = []
    for line_info in lines:
        variants.append(line_info.variant)
        quantities.append(line_info.line.quantity)
        products.append(line_info.product)

    products_translation = ProductTranslation.objects.filter(
        product__in=products, language_code=translation_language_code
    ).values("product_id", "name")
    product_translations = {
        product_translation["product_id"]: product_translation.get("name")
        for product_translation in products_translation
    }

    variants_translation = ProductVariantTranslation.objects.filter(
        product_variant__in=variants, language_code=translation_language_code
    ).values("product_variant_id", "name")
    variants_translation = {
        variant_translation["product_variant_id"]: variant_translation.get("name")
        for variant_translation in variants_translation
    }

    check_stock_quantity_bulk(variants, country_code, quantities)

    return [
        _create_line_for_order(
            manager,
            checkout,
            checkout_line_info,
            discounts,
            channel,
            product_translations,
            variants_translation,
        )
        for checkout_line_info in lines
    ]


def _prepare_order_data(
    *,
    manager: "PluginsManager",
    checkout: Checkout,
    lines: Iterable["CheckoutLineInfo"],
    discounts
) -> dict:
    """Run checks and return all the data from a given checkout to create an order.

    :raises NotApplicable InsufficientStock:
    """
    order_data = {}
    address = (
        checkout.shipping_address or checkout.billing_address
    )  # FIXME: check which address we need here

    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout=checkout,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    cards_total = checkout.get_total_gift_cards_balance()
    taxed_total.gross -= cards_total
    taxed_total.net -= cards_total

    taxed_total = max(taxed_total, zero_taxed_money(checkout.currency))

    shipping_total = manager.calculate_checkout_shipping(
        checkout, lines, address, discounts
    )
    shipping_tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout, lines, address, discounts, shipping_total
    )
    order_data.update(
        _process_shipping_data_for_order(checkout, shipping_total, manager, lines)
    )
    order_data.update(_process_user_data_for_order(checkout, manager))
    order_data.update(
        {
            "language_code": get_language(),
            "tracking_client_id": checkout.tracking_code or "",
            "total": taxed_total,
            "shipping_tax_rate": shipping_tax_rate,
        }
    )

    channel = checkout.channel
    order_data["lines"] = _create_lines_for_order(
        manager, checkout, lines, discounts, channel
    )

    # validate checkout gift cards
    _validate_gift_cards(checkout)

    # Get voucher data (last) as they require a transaction
    order_data.update(_get_voucher_data_for_order(checkout))

    # assign gift cards to the order

    order_data["total_price_left"] = (
        manager.calculate_checkout_subtotal(checkout, lines, address, discounts)
        + shipping_total
        - checkout.discount
    ).gross

    manager.preprocess_order_creation(checkout, discounts)
    return order_data


@transaction.atomic
def _create_order(*, checkout: Checkout, order_data: dict, user: User) -> Order:
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

    # TODO: refactor to use request.site / info.context site
    site_settings = Site.objects.get_current().settings
    status = (
        OrderStatus.UNFULFILLED
        if site_settings.automatically_confirm_all_new_orders
        else OrderStatus.UNCONFIRMED
    )
    order = Order.objects.create(
        **order_data,
        checkout_token=checkout.token,
        status=status,
        channel=checkout.channel,
    )
    for line in order_lines:
        line.order_id = order.pk
    order_lines = OrderLine.objects.bulk_create(order_lines)

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
    order.redirect_url = checkout.redirect_url
    order.private_metadata = checkout.private_metadata
    order.save()

    transaction.on_commit(lambda: order_created(order=order, user=user))

    # Send the order confirmation email
    transaction.on_commit(
        lambda: send_order_confirmation.delay(order.pk, checkout.redirect_url, user.pk)
    )
    transaction.on_commit(
        lambda: send_staff_order_confirmation.delay(order.pk, checkout.redirect_url)
    )

    return order


def _prepare_checkout(
    manager: "PluginsManager",
    checkout: models.Checkout,
    lines: Iterable["CheckoutLineInfo"],
    discounts,
    tracking_code,
    redirect_url,
    payment,
):
    """Prepare checkout object to complete the checkout process."""
    subtotal = manager.calculate_checkout_subtotal(
        checkout, lines, checkout.shipping_address, discounts
    )
    clean_checkout_shipping(checkout, lines, discounts, CheckoutErrorCode, subtotal)
    clean_checkout_payment(
        manager, checkout, lines, discounts, CheckoutErrorCode, last_payment=payment
    )
    if not checkout.channel.is_active:
        raise ValidationError(
            {
                "channel": ValidationError(
                    "Cannot complete checkout with inactive channel.",
                    code=CheckoutErrorCode.CHANNEL_INACTIVE.value,
                )
            }
        )
    if redirect_url:
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID.value
            )

    to_update = []
    if redirect_url and redirect_url != checkout.redirect_url:
        checkout.redirect_url = redirect_url
        to_update.append("redirect_url")

    if tracking_code and tracking_code != checkout.tracking_code:
        checkout.tracking_code = tracking_code
        to_update.append("tracking_code")

    if to_update:
        to_update.append("last_change")
        checkout.save(update_fields=to_update)


def release_voucher_usage(order_data: dict):
    voucher = order_data.get("voucher")
    if voucher:
        decrease_voucher_usage(voucher)
        if "user_email" in order_data:
            remove_voucher_usage_by_customer(voucher, order_data["user_email"])


def _get_order_data(
    manager: "PluginsManager",
    checkout: models.Checkout,
    lines: Iterable["CheckoutLineInfo"],
    discounts: List[DiscountInfo],
) -> dict:
    """Prepare data that will be converted to order and its lines."""
    try:
        order_data = _prepare_order_data(
            manager=manager,
            checkout=checkout,
            lines=lines,
            discounts=discounts,
        )
    except InsufficientStock as e:
        raise ValidationError(f"Insufficient product stock: {e.item}", code=e.code)
    except NotApplicable:
        raise ValidationError(
            "Voucher not applicable",
            code=CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.value,
        )
    except TaxError as tax_error:
        raise ValidationError(
            "Unable to calculate taxes - %s" % str(tax_error),
            code=CheckoutErrorCode.TAX_ERROR.value,
        )
    return order_data


def _process_payment(
    payment: Payment,
    store_source: bool,
    payment_data: Optional[dict],
    order_data: dict,
    plugin_manager: "PluginsManager",
) -> Transaction:
    """Process the payment assigned to checkout."""
    try:
        if payment.to_confirm:
            txn = gateway.confirm(payment, additional_data=payment_data)
        else:
            txn = gateway.process_payment(
                payment=payment,
                token=payment.token,
                store_source=store_source,
                additional_data=payment_data,
                plugin_manager=plugin_manager,
            )
        payment.refresh_from_db()
        if not txn.is_success:
            raise PaymentError(txn.error)
    except PaymentError as e:
        release_voucher_usage(order_data)
        raise ValidationError(str(e), code=CheckoutErrorCode.PAYMENT_ERROR.value)
    return txn


def complete_checkout(
    manager: "PluginsManager",
    checkout: models.Checkout,
    lines: Iterable["CheckoutLineInfo"],
    payment_data,
    store_source,
    discounts,
    user,
    tracking_code=None,
    redirect_url=None,
) -> Tuple[Optional[Order], bool, dict]:
    """Logic required to finalize the checkout and convert it to order.

    Should be used with transaction_with_commit_on_errors, as there is a possibility
    for thread race.
    :raises ValidationError
    """
    payment = checkout.get_last_active_payment()
    _prepare_checkout(
        manager=manager,
        checkout=checkout,
        lines=lines,
        discounts=discounts,
        tracking_code=tracking_code,
        redirect_url=redirect_url,
        payment=payment,
    )

    try:
        order_data = _get_order_data(manager, checkout, lines, discounts)
    except ValidationError as error:
        gateway.payment_refund_or_void(payment)
        raise error

    txn = _process_payment(
        payment=payment,  # type: ignore
        store_source=store_source,
        payment_data=payment_data,
        order_data=order_data,
        plugin_manager=manager,
    )

    if txn.customer_id and user.is_authenticated:
        store_customer_id(user, payment.gateway, txn.customer_id)  # type: ignore

    action_required = txn.action_required
    action_data = txn.action_required_data if action_required else {}

    order = None
    if not action_required:
        try:
            order = _create_order(
                checkout=checkout,
                order_data=order_data,
                user=user,  # type: ignore
            )
            # remove checkout after order is successfully created
            checkout.delete()
        except InsufficientStock as e:
            release_voucher_usage(order_data)
            gateway.payment_refund_or_void(payment)
            raise ValidationError(f"Insufficient product stock: {e.item}", code=e.code)

    return order, action_required, action_data
