from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)
from uuid import UUID

import graphene
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import transaction
from prices import Money, TaxedMoney

from ..account.error_codes import AccountErrorCode
from ..account.models import User
from ..account.utils import store_user_address
from ..checkout import calculations
from ..checkout.error_codes import CheckoutErrorCode
from ..core.exceptions import GiftCardNotApplicable, InsufficientStock
from ..core.postgres import FlatConcatSearchVector
from ..core.taxes import TaxError, zero_taxed_money
from ..core.tracing import traced_atomic_transaction
from ..core.utils.url import validate_storefront_url
from ..discount import DiscountInfo, DiscountValueType, OrderDiscountType, VoucherType
from ..discount.models import NotApplicable
from ..discount.utils import (
    add_voucher_usage_by_customer,
    get_sale_id_applied_as_a_discount,
    increase_voucher_usage,
    release_voucher_usage,
)
from ..graphql.checkout.utils import (
    prepare_insufficient_stock_checkout_validation_error,
)
from ..order import OrderOrigin, OrderStatus
from ..order.actions import mark_order_as_paid, order_created
from ..order.fetch import OrderInfo, OrderLineInfo
from ..order.models import Order, OrderLine
from ..order.notifications import send_order_confirmation
from ..order.search import prepare_order_search_vector_value
from ..order.utils import update_order_authorize_data, update_order_charge_data
from ..payment import PaymentError, TransactionKind, gateway
from ..payment.models import Payment, Transaction
from ..payment.utils import fetch_customer_id, store_customer_id
from ..product.models import ProductTranslation, ProductVariantTranslation
from ..warehouse.availability import check_stock_and_preorder_quantity_bulk
from ..warehouse.management import allocate_preorders, allocate_stocks
from ..warehouse.reservations import is_reservation_enabled
from . import AddressType
from .base_calculations import (
    calculate_base_line_unit_price,
    calculate_undiscounted_base_line_total_price,
    calculate_undiscounted_base_line_unit_price,
)
from .calculations import fetch_checkout_prices_if_expired
from .checkout_cleaner import (
    _validate_gift_cards,
    clean_checkout_payment,
    clean_checkout_shipping,
)
from .fetch import CheckoutInfo, CheckoutLineInfo
from .utils import get_voucher_for_checkout_info

if TYPE_CHECKING:
    from ..account.models import Address
    from ..app.models import App
    from ..discount.models import Voucher
    from ..plugins.manager import PluginsManager
    from ..site.models import SiteSettings
    from .models import Checkout


def _process_voucher_data_for_order(checkout_info: "CheckoutInfo") -> dict:
    """Fetch, process and return voucher/discount data from checkout.

    Careful! It should be called inside a transaction.
    If voucher has a usage limit, it will be increased!

    :raises NotApplicable: When the voucher is not applicable in the current checkout.
    """
    checkout = checkout_info.checkout
    voucher = get_voucher_for_checkout_info(checkout_info, with_lock=True)

    if checkout.voucher_code and not voucher:
        msg = "Voucher expired in meantime. Order placement aborted."
        raise NotApplicable(msg)

    if not voucher:
        return {}

    if voucher.usage_limit:
        increase_voucher_usage(voucher)
    if voucher.apply_once_per_customer:
        customer_email = cast(str, checkout_info.get_customer_email())
        add_voucher_usage_by_customer(voucher, customer_email)
    return {
        "voucher": voucher,
    }


def _process_shipping_data_for_order(
    checkout_info: "CheckoutInfo",
    shipping_price: TaxedMoney,
    manager: "PluginsManager",
    lines: Iterable["CheckoutLineInfo"],
) -> Dict[str, Any]:
    """Fetch, process and return shipping data from checkout."""
    delivery_method_info = checkout_info.delivery_method_info
    shipping_address = delivery_method_info.shipping_address

    if (
        delivery_method_info.store_as_customer_address
        and checkout_info.user
        and shipping_address
    ):
        store_user_address(
            checkout_info.user, shipping_address, AddressType.SHIPPING, manager=manager
        )
        if checkout_info.user.addresses.filter(pk=shipping_address.pk).exists():
            shipping_address = shipping_address.get_copy()

    result: Dict[str, Any] = {
        "shipping_address": shipping_address,
        "shipping_price": shipping_price,
        "weight": checkout_info.checkout.get_total_weight(lines),
    }
    result.update(delivery_method_info.delivery_method_order_field)
    result.update(delivery_method_info.delivery_method_name)

    return result


def _process_user_data_for_order(checkout_info: "CheckoutInfo", manager):
    """Fetch, process and return shipping data from checkout."""
    billing_address = checkout_info.billing_address

    if checkout_info.user and billing_address:
        store_user_address(
            checkout_info.user, billing_address, AddressType.BILLING, manager=manager
        )
        if checkout_info.user.addresses.filter(pk=billing_address.pk).exists():
            billing_address = billing_address.get_copy()

    return {
        "user": checkout_info.user,
        "user_email": checkout_info.get_customer_email(),
        "billing_address": billing_address,
        "customer_note": checkout_info.checkout.note,
    }


def _create_line_for_order(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable[DiscountInfo],
    products_translation: Dict[int, Optional[str]],
    variants_translation: Dict[int, Optional[str]],
    taxes_included_in_prices: bool,
) -> OrderLineInfo:
    """Create a line for the given order.

    :raises InsufficientStock: when there is not enough items in stock for this variant.
    """
    checkout_line = checkout_line_info.line
    quantity = checkout_line.quantity
    variant = checkout_line_info.variant
    product = checkout_line_info.product

    product_name = str(product)
    variant_name = str(variant)

    translated_product_name = products_translation.get(product.id, "")
    translated_variant_name = variants_translation.get(variant.id, "")

    if translated_product_name == product_name:
        translated_product_name = ""

    if translated_variant_name == variant_name:
        translated_variant_name = ""

    base_unit_price = calculate_base_line_unit_price(
        line_info=checkout_line_info, channel=checkout_info.channel, discounts=discounts
    )
    undiscounted_base_unit_price = calculate_undiscounted_base_line_unit_price(
        line_info=checkout_line_info,
        channel=checkout_info.channel,
    )
    undiscounted_base_total_price = calculate_undiscounted_base_line_total_price(
        line_info=checkout_line_info,
        channel=checkout_info.channel,
    )
    undiscounted_unit_price = TaxedMoney(
        net=undiscounted_base_unit_price, gross=undiscounted_base_unit_price
    )
    undiscounted_total_price = TaxedMoney(
        net=undiscounted_base_total_price, gross=undiscounted_base_total_price
    )
    total_line_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=checkout_line_info,
        discounts=discounts,
    )
    unit_price = calculations.checkout_line_unit_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=checkout_line_info,
        discounts=discounts,
    )
    tax_rate = calculations.checkout_line_tax_rate(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=checkout_line_info,
        discounts=discounts,
    )

    price_override = checkout_line_info.line.price_override
    channel_listing = checkout_line_info.channel_listing
    price = (
        channel_listing.price
        if price_override is None
        else Money(price_override, channel_listing.currency)
    )
    sale_id = get_sale_id_applied_as_a_discount(
        product=checkout_line_info.product,
        price=price,
        discounts=discounts,
        collections=checkout_line_info.collections,
        channel=checkout_info.channel,
        variant_id=checkout_line_info.variant.id,
    )

    voucher_code = None
    if checkout_line_info.voucher:
        voucher_code = checkout_line_info.voucher.code

    discount_price = undiscounted_unit_price - unit_price
    if taxes_included_in_prices:
        discount_amount = discount_price.gross
    else:
        discount_amount = discount_price.net

    unit_discount_reason = None
    if sale_id:
        unit_discount_reason = "Sale: %s" % graphene.Node.to_global_id("Sale", sale_id)
    if voucher_code:
        if unit_discount_reason:
            unit_discount_reason += f" & Voucher code: {voucher_code}"
        else:
            unit_discount_reason = f"Voucher code: {voucher_code}"

    line = OrderLine(
        product_name=product_name,
        variant_name=variant_name,
        translated_product_name=translated_product_name,
        translated_variant_name=translated_variant_name,
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,  # type: ignore
        undiscounted_unit_price=undiscounted_unit_price,  # type: ignore
        undiscounted_total_price=undiscounted_total_price,  # type: ignore
        total_price=total_line_price,  # type: ignore
        tax_rate=tax_rate,
        sale_id=graphene.Node.to_global_id("Sale", sale_id) if sale_id else None,
        voucher_code=voucher_code,
        unit_discount=discount_amount,  # type: ignore
        unit_discount_reason=unit_discount_reason,
        unit_discount_value=discount_amount.amount,  # we store value as fixed discount
        base_unit_price=base_unit_price,
        undiscounted_base_unit_price=undiscounted_base_unit_price,
        metadata=checkout_line.metadata,
        private_metadata=checkout_line.private_metadata,
    )
    is_digital = line.is_digital
    line_info = OrderLineInfo(
        line=line,
        quantity=quantity,
        is_digital=is_digital,
        variant=variant,
        digital_content=variant.digital_content if is_digital and variant else None,
        warehouse_pk=checkout_info.delivery_method_info.warehouse_pk,
    )

    return line_info


def _create_lines_for_order(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    discounts: Iterable[DiscountInfo],
    check_reservations: bool,
    taxes_included_in_prices: bool,
) -> Iterable[OrderLineInfo]:
    """Create a lines for the given order.

    :raises InsufficientStock: when there is not enough items in stock for this variant.
    """
    translation_language_code = checkout_info.checkout.language_code
    country_code = checkout_info.get_country()

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

    additional_warehouse_lookup = (
        checkout_info.delivery_method_info.get_warehouse_filter_lookup()
    )
    check_stock_and_preorder_quantity_bulk(
        variants,
        country_code,
        quantities,
        checkout_info.channel.slug,
        global_quantity_limit=None,
        delivery_method_info=checkout_info.delivery_method_info,
        additional_filter_lookup=additional_warehouse_lookup,
        existing_lines=lines,
        replace=True,
        check_reservations=check_reservations,
    )

    return [
        _create_line_for_order(
            manager,
            checkout_info,
            lines,
            checkout_line_info,
            discounts,
            product_translations,
            variants_translation,
            taxes_included_in_prices,
        )
        for checkout_line_info in lines
    ]


def _prepare_order_data(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    discounts: Iterable["DiscountInfo"],
    taxes_included_in_prices: bool,
    check_reservations: bool = False,
) -> dict:
    """Run checks and return all the data from a given checkout to create an order.

    :raises NotApplicable InsufficientStock:
    """
    checkout = checkout_info.checkout
    order_data = {}
    address = (
        checkout_info.shipping_address or checkout_info.billing_address
    )  # FIXME: check which address we need here

    taxed_total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    undiscounted_total = taxed_total + checkout.discount

    shipping_total = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    shipping_tax_rate = calculations.checkout_shipping_tax_rate(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    order_data.update(
        _process_shipping_data_for_order(checkout_info, shipping_total, manager, lines)
    )
    order_data.update(_process_user_data_for_order(checkout_info, manager))
    order_data.update(
        {
            "language_code": checkout.language_code,
            "tracking_client_id": checkout.tracking_code or "",
            "total": taxed_total,
            "undiscounted_total": undiscounted_total,
            "shipping_tax_rate": shipping_tax_rate,
        }
    )

    order_data["lines"] = _create_lines_for_order(
        manager,
        checkout_info,
        lines,
        discounts,
        check_reservations,
        taxes_included_in_prices,
    )

    # validate checkout gift cards
    _validate_gift_cards(checkout)

    order_data.update(_process_voucher_data_for_order(checkout_info))

    order_data["total_price_left"] = (
        calculations.checkout_subtotal(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=address,
            discounts=discounts,
        )
        + shipping_total
        - checkout.discount
    ).gross

    try:
        manager.preprocess_order_creation(checkout_info, discounts, lines)
    except TaxError:
        release_voucher_usage(order_data.get("voucher"), order_data.get("user_email"))
        raise

    return order_data


@traced_atomic_transaction()
def _create_order(
    *,
    checkout_info: "CheckoutInfo",
    checkout_lines: Iterable["CheckoutLineInfo"],
    order_data: dict,
    user: User,
    app: Optional["App"],
    manager: "PluginsManager",
    site_settings=None
) -> Order:
    """Create an order from the checkout.

    Each order will get a private copy of both the billing and the shipping
    address (if shipping).

    If any of the addresses is new and the user is logged in the address
    will also get saved to that user's address book.

    Current user's language is saved in the order so we can later determine
    which language to use when sending email.
    """
    from ..order.utils import add_gift_cards_to_order

    checkout = checkout_info.checkout
    order = Order.objects.filter(checkout_token=checkout.token).first()
    if order is not None:
        return order

    total_price_left = order_data.pop("total_price_left")
    order_lines_info = order_data.pop("lines")

    if site_settings is None:
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
        origin=OrderOrigin.CHECKOUT,
        channel=checkout_info.channel,
        should_refresh_prices=False,
    )
    if checkout.discount:
        # store voucher as a fixed value as it this the simplest solution for now.
        # This will be solved when we refactor the voucher logic to use .discounts
        # relations
        voucher = order_data.get("voucher")
        # When we have a voucher for specific products we track it directly in the
        # Orderline. Voucher with 'apply_once_per_order' is handled in the same way
        # as we apply it only for single quantity of the cheapest item.
        if not voucher or (
            voucher.type != VoucherType.SPECIFIC_PRODUCT
            and not voucher.apply_once_per_order
        ):
            order.discounts.create(
                type=OrderDiscountType.VOUCHER,
                value_type=DiscountValueType.FIXED,
                value=checkout.discount.amount,
                name=checkout.discount_name,
                translated_name=checkout.translated_discount_name,
                currency=checkout.currency,
                amount_value=checkout.discount_amount,
            )

    order_lines = []
    for line_info in order_lines_info:
        line = line_info.line
        line.order_id = order.pk
        order_lines.append(line)

    OrderLine.objects.bulk_create(order_lines)

    country_code = checkout_info.get_country()
    additional_warehouse_lookup = (
        checkout_info.delivery_method_info.get_warehouse_filter_lookup()
    )
    allocate_stocks(
        order_lines_info,
        country_code,
        checkout_info.channel,
        manager,
        checkout_info.delivery_method_info.warehouse_pk,
        additional_warehouse_lookup,
        check_reservations=is_reservation_enabled(site_settings),
        checkout_lines=[line.line for line in checkout_lines],
    )
    allocate_preorders(
        order_lines_info,
        checkout_info.channel.slug,
        check_reservations=is_reservation_enabled(site_settings),
        checkout_lines=[line.line for line in checkout_lines],
    )

    add_gift_cards_to_order(checkout_info, order, total_price_left, user, app)

    # assign checkout payments to the order
    checkout.payments.update(order=order)

    # copy metadata from the checkout into the new order
    order.metadata = checkout.metadata
    order.redirect_url = checkout.redirect_url
    order.private_metadata = checkout.private_metadata
    update_order_charge_data(order, with_save=False)
    update_order_authorize_data(order, with_save=False)
    order.search_vector = FlatConcatSearchVector(
        *prepare_order_search_vector_value(order)
    )
    order.save()

    order_info = OrderInfo(
        order=order,
        customer_email=order_data["user_email"],
        channel=checkout_info.channel,
        payment=order.get_last_payment(),
        lines_data=order_lines_info,
    )

    transaction.on_commit(
        lambda: order_created(
            order_info=order_info,
            user=user,
            app=app,
            manager=manager,
            site_settings=site_settings,
        )
    )

    # Send the order confirmation email
    transaction.on_commit(
        lambda: send_order_confirmation(order_info, checkout.redirect_url, manager)
    )

    return order


def _prepare_checkout(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    discounts,
    tracking_code,
    redirect_url,
    payment,
):
    """Prepare checkout object to complete the checkout process."""
    checkout = checkout_info.checkout
    clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)
    clean_checkout_payment(
        manager,
        checkout_info,
        lines,
        discounts,
        CheckoutErrorCode,
        last_payment=payment,
    )
    if not checkout_info.channel.is_active:
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

    if tracking_code and str(tracking_code) != checkout.tracking_code:
        checkout.tracking_code = tracking_code
        to_update.append("tracking_code")

    if to_update:
        to_update.append("last_change")
        checkout.save(update_fields=to_update)


def _get_order_data(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    discounts: List[DiscountInfo],
    site_settings: "SiteSettings",
) -> dict:
    """Prepare data that will be converted to order and its lines."""
    try:
        order_data = _prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            discounts=discounts,
            check_reservations=is_reservation_enabled(site_settings),
            taxes_included_in_prices=site_settings.include_taxes_in_prices,
        )
    except InsufficientStock as e:
        error = prepare_insufficient_stock_checkout_validation_error(e)
        raise error
    except NotApplicable:
        raise ValidationError(
            "Voucher not applicable",
            code=CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.value,
        )
    except GiftCardNotApplicable as e:
        raise ValidationError(e.message, code=e.code)
    except TaxError as tax_error:
        raise ValidationError(
            "Unable to calculate taxes - %s" % str(tax_error),
            code=CheckoutErrorCode.TAX_ERROR.value,
        )
    return order_data


def _process_payment(
    payment: Payment,
    customer_id: Optional[str],
    store_source: bool,
    payment_data: Optional[dict],
    order_data: dict,
    manager: "PluginsManager",
    channel_slug: str,
) -> Transaction:
    """Process the payment assigned to checkout."""
    try:
        if payment.to_confirm:
            txn = gateway.confirm(
                payment,
                manager,
                additional_data=payment_data,
                channel_slug=channel_slug,
            )
        else:
            txn = gateway.process_payment(
                payment=payment,
                token=payment.token,
                manager=manager,
                customer_id=customer_id,
                store_source=store_source,
                additional_data=payment_data,
                channel_slug=channel_slug,
            )
        payment.refresh_from_db()
        if not txn.is_success:
            raise PaymentError(txn.error)
    except PaymentError as e:
        release_voucher_usage(order_data.get("voucher"), order_data.get("user_email"))
        raise ValidationError(str(e), code=CheckoutErrorCode.PAYMENT_ERROR.value)
    return txn


def complete_checkout(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    payment_data,
    store_source,
    discounts,
    user,
    app,
    site_settings=None,
    tracking_code=None,
    redirect_url=None,
) -> Tuple[Optional[Order], bool, dict]:
    """Logic required to finalize the checkout and convert it to order.

    Should be used with transaction_with_commit_on_errors, as there is a possibility
    for thread race.
    :raises ValidationError
    """

    fetch_checkout_prices_if_expired(checkout_info, manager, lines, discounts)

    checkout = checkout_info.checkout
    channel_slug = checkout_info.channel.slug
    payment = checkout.get_last_active_payment()
    _prepare_checkout(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        discounts=discounts,
        tracking_code=tracking_code,
        redirect_url=redirect_url,
        payment=payment,
    )

    if site_settings is None:
        site_settings = Site.objects.get_current().settings

    try:
        order_data = _get_order_data(
            manager, checkout_info, lines, discounts, site_settings
        )
    except ValidationError as exc:
        gateway.payment_refund_or_void(payment, manager, channel_slug=channel_slug)
        raise exc

    customer_id = None
    if payment and user.is_authenticated:
        customer_id = fetch_customer_id(user=user, gateway=payment.gateway)

    action_required = False
    action_data: Dict[str, str] = {}
    if payment:
        txn = _process_payment(
            payment=payment,  # type: ignore
            customer_id=customer_id,
            store_source=store_source,
            payment_data=payment_data,
            order_data=order_data,
            manager=manager,
            channel_slug=channel_slug,
        )

        if txn.customer_id and user.is_authenticated:
            store_customer_id(user, payment.gateway, txn.customer_id)  # type: ignore

        action_required = txn.action_required
        if action_required:
            action_data = txn.action_required_data
            release_voucher_usage(
                order_data.get("voucher"), order_data.get("user_email")
            )

    order = None
    if not action_required and not _is_refund_ongoing(payment):
        try:
            order = _create_order(
                checkout_info=checkout_info,
                checkout_lines=lines,
                order_data=order_data,
                user=user,  # type: ignore
                app=app,
                manager=manager,
                site_settings=site_settings,
            )
            # remove checkout after order is successfully created
            checkout.delete()
        except InsufficientStock as e:
            release_voucher_usage(
                order_data.get("voucher"), order_data.get("user_email")
            )
            gateway.payment_refund_or_void(payment, manager, channel_slug=channel_slug)
            error = prepare_insufficient_stock_checkout_validation_error(e)
            raise error
        except GiftCardNotApplicable as e:
            release_voucher_usage(
                order_data.get("voucher"), order_data.get("user_email")
            )
            gateway.payment_refund_or_void(payment, manager, channel_slug=channel_slug)
            raise ValidationError(code=e.code, message=e.message)

        # if the order total value is 0 it is paid from the definition
        if order.total.net.amount == 0:
            mark_order_as_paid(order, user, app, manager)

    return order, action_required, action_data


def _is_refund_ongoing(payment):
    """Return True if refund is ongoing for given payment."""
    return (
        payment.transactions.filter(
            kind=TransactionKind.REFUND_ONGOING, is_success=True
        ).exists()
        if payment
        else False
    )


def _get_order_total(
    checkout_info: CheckoutInfo,
    lines: List[CheckoutLineInfo],
    discounts: List["DiscountInfo"],
    manager: "PluginsManager",
    address: Optional["Address"],
) -> TaxedMoney:
    """Calculate a taxed total for order."""
    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    cards_total = checkout_info.checkout.get_total_gift_cards_balance()
    taxed_total.gross -= cards_total
    taxed_total.net -= cards_total
    taxed_total = max(taxed_total, zero_taxed_money(checkout_info.checkout.currency))
    return taxed_total


def _increase_voucher_usage(checkout_info: "CheckoutInfo"):
    """Increase a voucher usage applied to the checkout."""
    voucher = get_voucher_for_checkout_info(checkout_info, with_lock=True)
    if not voucher:
        return None

    if voucher.apply_once_per_customer:
        customer_email = cast(str, checkout_info.get_customer_email())
        add_voucher_usage_by_customer(voucher, customer_email)

    if voucher.usage_limit:
        increase_voucher_usage(voucher)


def _create_order_lines_from_checkout_lines(
    checkout_info: CheckoutInfo,
    lines: List[CheckoutLineInfo],
    discounts: List["DiscountInfo"],
    manager: "PluginsManager",
    order_pk: Union[str, UUID],
    reservation_enabled: bool,
    taxes_included_in_prices: bool,
) -> List[OrderLineInfo]:
    order_lines_info = _create_lines_for_order(
        manager,
        checkout_info,
        lines,
        discounts,
        reservation_enabled,
        taxes_included_in_prices,
    )
    order_lines = []
    for line_info in order_lines_info:
        line = line_info.line
        line.order_id = order_pk
        order_lines.append(line)

    OrderLine.objects.bulk_create(order_lines)
    return list(order_lines_info)


def _handle_allocations_of_order_lines(
    checkout_info: CheckoutInfo,
    checkout_lines: List[CheckoutLineInfo],
    order_lines_info: List[OrderLineInfo],
    manager: "PluginsManager",
    reservation_enabled: bool,
):
    country_code = checkout_info.get_country()
    additional_warehouse_lookup = (
        checkout_info.delivery_method_info.get_warehouse_filter_lookup()
    )
    allocate_stocks(
        order_lines_info,
        country_code,
        checkout_info.channel,
        manager,
        checkout_info.delivery_method_info.warehouse_pk,
        additional_warehouse_lookup,
        check_reservations=reservation_enabled,
        checkout_lines=[line.line for line in checkout_lines],
    )
    allocate_preorders(
        order_lines_info,
        checkout_info.channel.slug,
        check_reservations=reservation_enabled,
        checkout_lines=[line.line for line in checkout_lines],
    )


def _handle_checkout_discount(
    order: "Order", checkout: "Checkout", voucher: Optional["Voucher"]
):
    if checkout.discount:
        # store voucher as a fixed value as it this the simplest solution for now.
        # This will be solved when we refactor the voucher logic to use .discounts
        # relations

        # When we have a voucher for specific products we track it directly in the
        # Orderline. Voucher with 'apply_once_per_order' is handled in the same way
        # as we apply it only for single quantity of the cheapest item.
        if not voucher or (
            voucher.type != VoucherType.SPECIFIC_PRODUCT
            and not voucher.apply_once_per_order
        ):
            order.discounts.create(
                type=OrderDiscountType.VOUCHER,
                value_type=DiscountValueType.FIXED,
                value=checkout.discount.amount,
                name=checkout.discount_name,
                translated_name=checkout.translated_discount_name,
                currency=checkout.currency,
                amount_value=checkout.discount_amount,
            )


def _post_create_order_actions(
    order: "Order",
    checkout_info: "CheckoutInfo",
    order_lines_info: List["OrderLineInfo"],
    manager: "PluginsManager",
    user: User,
    app: Optional["App"],
    site_settings: "SiteSettings",
):
    order_info = OrderInfo(
        order=order,
        customer_email=order.user_email,
        channel=checkout_info.channel,
        payment=order.get_last_payment(),
        lines_data=order_lines_info,
    )

    transaction.on_commit(
        lambda: order_created(
            order_info=order_info,
            user=user,
            app=app,
            manager=manager,
            site_settings=site_settings,
        )
    )

    # Send the order confirmation email
    transaction.on_commit(
        lambda: send_order_confirmation(
            order_info, checkout_info.checkout.redirect_url, manager
        )
    )


def _create_order_from_checkout(
    checkout_info: CheckoutInfo,
    checkout_lines_info: List[CheckoutLineInfo],
    discounts: List["DiscountInfo"],
    manager: "PluginsManager",
    user: User,
    app: Optional["App"],
    tracking_code: Optional[str] = None,
):
    from ..order.utils import add_gift_cards_to_order

    site_settings = Site.objects.get_current().settings

    address = checkout_info.shipping_address or checkout_info.billing_address

    reservation_enabled = is_reservation_enabled(site_settings)
    taxes_included_in_prices = site_settings.include_taxes_in_prices

    # total
    taxed_total = _get_order_total(
        checkout_info,
        checkout_lines_info,
        discounts,
        manager,
        address,
    )
    undiscounted_total = taxed_total + checkout_info.checkout.discount

    # voucher
    voucher = checkout_info.voucher

    # shipping
    shipping_total = manager.calculate_checkout_shipping(
        checkout_info, checkout_lines_info, address, discounts
    )
    shipping_tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info, checkout_lines_info, address, discounts, shipping_total
    )

    # status
    status = (
        OrderStatus.UNFULFILLED
        if site_settings.automatically_confirm_all_new_orders
        else OrderStatus.UNCONFIRMED
    )

    # order
    order = Order.objects.create(
        status=status,
        language_code=checkout_info.checkout.language_code,
        tracking_client_id=tracking_code or "",
        total=taxed_total,
        undiscounted_total=undiscounted_total,
        shipping_tax_rate=shipping_tax_rate,
        voucher=voucher,
        checkout_token=checkout_info.checkout.token,
        origin=OrderOrigin.CHECKOUT,
        channel=checkout_info.channel,
        metadata=checkout_info.checkout.metadata,
        private_metadata=checkout_info.checkout.private_metadata,
        redirect_url=checkout_info.checkout.redirect_url,
        should_refresh_prices=False,
        **_process_shipping_data_for_order(
            checkout_info, shipping_total, manager, checkout_lines_info
        ),
        **_process_user_data_for_order(checkout_info, manager),
    )

    # checkout discount
    _handle_checkout_discount(order, checkout_info.checkout, voucher)

    # lines
    order_lines_info = _create_order_lines_from_checkout_lines(
        checkout_info=checkout_info,
        lines=checkout_lines_info,
        discounts=discounts,
        manager=manager,
        order_pk=order.pk,
        reservation_enabled=reservation_enabled,
        taxes_included_in_prices=taxes_included_in_prices,
    )

    # allocations
    _handle_allocations_of_order_lines(
        checkout_info=checkout_info,
        checkout_lines=checkout_lines_info,
        order_lines_info=order_lines_info,
        manager=manager,
        reservation_enabled=reservation_enabled,
    )

    # giftcards
    currency = checkout_info.checkout.currency
    subtotal_list = [line.line.total_price for line in order_lines_info]
    subtotal = sum(subtotal_list, zero_taxed_money(currency))
    total_without_giftcard = subtotal + shipping_total - checkout_info.checkout.discount
    add_gift_cards_to_order(
        checkout_info, order, total_without_giftcard.gross, user, app
    )

    # payments
    checkout_info.checkout.payments.update(order=order, checkout_id=None)
    checkout_info.checkout.payment_transactions.update(order=order, checkout_id=None)
    update_order_charge_data(order, with_save=False)
    update_order_authorize_data(order, with_save=False)

    # order search
    order.search_vector = FlatConcatSearchVector(
        *prepare_order_search_vector_value(order)
    )
    order.save()

    # post create actions
    _post_create_order_actions(
        order=order,
        checkout_info=checkout_info,
        order_lines_info=order_lines_info,
        manager=manager,
        user=user,
        app=app,
        site_settings=site_settings,
    )
    return order


def create_order_from_checkout(
    checkout_info: CheckoutInfo,
    checkout_lines: Iterable["CheckoutLineInfo"],
    discounts: List["DiscountInfo"],
    manager: "PluginsManager",
    user: User,
    app: Optional["App"],
    tracking_code: str,
    delete_checkout: bool = True,
) -> Order:
    """Crate order from checkout.

    If checkout doesn't have all required data, the function will raise ValidationError.

    Each order will get a private copy of both the billing and the shipping
    address (if shipping).

    If any of the addresses is new and the user is logged in the address
    will also get saved to that user's address book.

    Current user's language is saved in the order so we can later determine
    which language to use when sending email.

    Checkout can be deleted by setting flag `delete_checkout` to True

    :raises: InsufficientStock, GiftCardNotApplicable
    """

    if checkout_info.voucher:
        with transaction.atomic():
            _increase_voucher_usage(checkout_info=checkout_info)

    with transaction.atomic():
        try:
            order = _create_order_from_checkout(
                checkout_info=checkout_info,
                checkout_lines_info=list(checkout_lines),
                discounts=discounts,
                manager=manager,
                user=user,
                app=app,
                tracking_code=tracking_code,
            )
            if delete_checkout:
                checkout_info.checkout.delete()
            return order
        except InsufficientStock:
            release_voucher_usage(
                checkout_info.voucher, checkout_info.checkout.get_customer_email()
            )
            raise
        except GiftCardNotApplicable:
            release_voucher_usage(
                checkout_info.voucher, checkout_info.checkout.get_customer_email()
            )
            raise
