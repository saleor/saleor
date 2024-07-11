import logging
from collections.abc import Iterable
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional, Union, cast
from uuid import UUID

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.models import model_to_dict
from django.utils import timezone
from prices import Money, TaxedMoney

from ..account.error_codes import AccountErrorCode
from ..account.models import User
from ..account.utils import retrieve_user_by_email, store_user_address
from ..channel import MarkAsPaidStrategy
from ..checkout import CheckoutAuthorizeStatus, calculations
from ..checkout.error_codes import CheckoutErrorCode
from ..core.exceptions import GiftCardNotApplicable, InsufficientStock
from ..core.postgres import FlatConcatSearchVector
from ..core.taxes import TaxError, zero_taxed_money
from ..core.tracing import traced_atomic_transaction
from ..core.transactions import transaction_with_commit_on_errors
from ..core.utils.url import validate_storefront_url
from ..discount import DiscountType, DiscountValueType
from ..discount.models import CheckoutDiscount, NotApplicable, OrderLineDiscount
from ..discount.utils.promotion import get_sale_id
from ..discount.utils.voucher import (
    increase_voucher_usage,
    release_voucher_code_usage,
)
from ..graphql.checkout.utils import (
    prepare_insufficient_stock_checkout_validation_error,
)
from ..order import OrderOrigin, OrderStatus
from ..order.actions import mark_order_as_paid_with_payment, order_created
from ..order.fetch import OrderInfo, OrderLineInfo
from ..order.models import Order, OrderLine
from ..order.notifications import send_order_confirmation
from ..order.search import prepare_order_search_vector_value
from ..order.utils import (
    update_order_authorize_data,
    update_order_charge_data,
    update_order_display_gross_prices,
)
from ..payment import PaymentError, TransactionKind, gateway
from ..payment.model_helpers import get_subtotal
from ..payment.models import Payment, Transaction
from ..payment.utils import fetch_customer_id, store_customer_id
from ..product.models import ProductTranslation, ProductVariantTranslation
from ..tax.calculations import get_taxed_undiscounted_price
from ..tax.utils import (
    get_shipping_tax_class_kwargs_for_order,
    get_tax_class_kwargs_for_order_line,
)
from ..warehouse.availability import check_stock_and_preorder_quantity_bulk
from ..warehouse.management import allocate_preorders, allocate_stocks
from ..warehouse.models import Reservation, Stock
from ..warehouse.reservations import is_reservation_enabled
from . import AddressType
from .base_calculations import (
    base_checkout_delivery_price,
    calculate_base_line_unit_price,
    calculate_undiscounted_base_line_total_price,
    calculate_undiscounted_base_line_unit_price,
)
from .calculations import fetch_checkout_data
from .checkout_cleaner import (
    _validate_gift_cards,
    clean_billing_address,
    clean_checkout_payment,
    clean_checkout_shipping,
)
from .fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from .models import Checkout
from .utils import (
    calculate_checkout_weight,
    get_checkout_metadata,
    get_or_create_checkout_metadata,
    get_voucher_for_checkout_info,
)

if TYPE_CHECKING:
    from ..app.models import App
    from ..discount.models import Voucher, VoucherCode
    from ..plugins.manager import PluginsManager
    from ..site.models import SiteSettings

logger = logging.getLogger(__name__)


def _process_voucher_data_for_order(checkout_info: "CheckoutInfo") -> dict:
    """Fetch, process and return voucher/discount data from checkout.

    Careful! It should be called inside a transaction.
    If voucher has a usage limit, it will be increased!

    :raises NotApplicable: When the voucher is not applicable in the current checkout.
    """
    checkout = checkout_info.checkout
    voucher, voucher_code = get_voucher_for_checkout_info(checkout_info, with_lock=True)

    if checkout.voucher_code and not voucher_code:
        msg = "Voucher expired in meantime. Order placement aborted."
        raise NotApplicable(msg)

    if not voucher_code or not voucher:
        return {}

    customer_email = cast(str, checkout_info.get_customer_email())

    _increase_checkout_voucher_usage(checkout, voucher_code, voucher, customer_email)
    return {
        "voucher": voucher,
        "voucher_code": voucher_code.code,
    }


@traced_atomic_transaction()
def _increase_checkout_voucher_usage(
    checkout: "Checkout",
    voucher_code: "VoucherCode",
    voucher: "Voucher",
    customer_email: str,
):
    # Prevent race condition when two different threads are processing the same checkout
    # with limited usage voucher assigned, both threads increasing the
    # voucher usage which causing `NotApplicable` error for voucher.
    if checkout.is_voucher_usage_increased:
        return

    increase_voucher_usage(voucher, voucher_code, customer_email)
    checkout.is_voucher_usage_increased = True
    checkout.save(update_fields=["is_voucher_usage_increased"])


@traced_atomic_transaction()
def _release_checkout_voucher_usage(
    checkout: "Checkout",
    voucher_code: Optional["VoucherCode"],
    voucher: Optional["Voucher"],
    user_email: Optional[str],
    checkout_update_fields: Optional[list[str]] = None,
):
    if not checkout.is_voucher_usage_increased:
        return

    checkout.is_voucher_usage_increased = False
    if checkout_update_fields is None:
        checkout.save(update_fields=["is_voucher_usage_increased"])
    else:
        checkout_update_fields.append("is_voucher_usage_increased")

    if voucher_code:
        release_voucher_code_usage(
            voucher_code,
            voucher,
            user_email,
        )


def _process_shipping_data_for_order(
    checkout_info: "CheckoutInfo",
    base_shipping_price: Money,
    shipping_price: TaxedMoney,
    manager: "PluginsManager",
    lines: Iterable["CheckoutLineInfo"],
) -> dict[str, Any]:
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

    if shipping_address and delivery_method_info.warehouse_pk:
        shipping_address = shipping_address.get_copy()

    shipping_method = delivery_method_info.delivery_method
    tax_class = getattr(shipping_method, "tax_class", None)

    result: dict[str, Any] = {
        "shipping_address": shipping_address,
        "base_shipping_price": base_shipping_price,
        "shipping_price": shipping_price,
        "weight": calculate_checkout_weight(lines),
        **get_shipping_tax_class_kwargs_for_order(tax_class),
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
    products_translation: dict[int, Optional[str]],
    variants_translation: dict[int, Optional[str]],
    prices_entered_with_tax: bool,
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

    # the price with sale and discounts applied - base price that is used for
    # total price calculation
    base_unit_price = calculate_base_line_unit_price(line_info=checkout_line_info)
    # the unit price before applying any discount (sale or voucher)
    undiscounted_base_unit_price = calculate_undiscounted_base_line_unit_price(
        line_info=checkout_line_info,
        channel=checkout_info.channel,
    )
    # the total price before applying any discount (sale or voucher)
    undiscounted_base_total_price = calculate_undiscounted_base_line_total_price(
        line_info=checkout_line_info,
        channel=checkout_info.channel,
    )
    # total price after applying all discounts - sales and vouchers
    total_line_price = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=checkout_line_info,
    )
    # unit price after applying all discounts - sales and vouchers
    unit_price = calculations.checkout_line_unit_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=checkout_line_info,
    )
    tax_rate = calculations.checkout_line_tax_rate(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=checkout_line_info,
    )
    # unit price before applying discounts
    undiscounted_unit_price = get_taxed_undiscounted_price(
        undiscounted_base_unit_price,
        unit_price,
        tax_rate,
        prices_entered_with_tax,
    )
    # total price before applying discounts
    undiscounted_total_price = get_taxed_undiscounted_price(
        undiscounted_base_total_price,
        total_line_price,
        tax_rate,
        prices_entered_with_tax,
    )

    discount_price = undiscounted_unit_price - unit_price
    if prices_entered_with_tax:
        discount_amount = discount_price.gross
    else:
        discount_amount = discount_price.net

    voucher_code = checkout_info.checkout.voucher_code
    is_line_voucher_code = bool(checkout_line_info.voucher)
    unit_discount_reason = _get_unit_discount_reason(voucher_code, is_line_voucher_code)

    tax_class = None
    if product.tax_class_id:
        tax_class = product.tax_class
    else:
        tax_class = product.product_type.tax_class

    is_price_overridden = checkout_line.price_override is not None

    line = OrderLine(  # type: ignore[misc] # see below:
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
        is_gift=checkout_line.is_gift,
        unit_price=unit_price,  # money field not supported by mypy_django_plugin
        undiscounted_unit_price=undiscounted_unit_price,  # money field not supported by mypy_django_plugin # noqa: E501
        undiscounted_total_price=undiscounted_total_price,  # money field not supported by mypy_django_plugin # noqa: E501
        total_price=total_line_price,
        tax_rate=tax_rate,
        voucher_code=voucher_code if is_line_voucher_code else None,
        unit_discount=discount_amount,  # money field not supported by mypy_django_plugin # noqa: E501
        unit_discount_reason=unit_discount_reason,
        unit_discount_value=discount_amount.amount,  # we store value as fixed discount
        unit_discount_type=DiscountValueType.FIXED,
        base_unit_price=base_unit_price,  # money field not supported by mypy_django_plugin # noqa: E501
        undiscounted_base_unit_price=undiscounted_base_unit_price,  # money field not supported by mypy_django_plugin # noqa: E501
        is_price_overridden=is_price_overridden,
        metadata=checkout_line.metadata,
        private_metadata=checkout_line.private_metadata,
        **get_tax_class_kwargs_for_order_line(tax_class),
    )

    line_discounts = _create_order_line_discounts(checkout_line_info, line)
    if line_discounts:
        # We might have catalogue and gift predicate promotion so there might be more
        # than one sale_id.
        # The sale_id will be set only for the catalogue discount if exists.
        line.sale_id = _get_sale_id(line_discounts)
        promotion_discount_reason = " & ".join(
            [discount.reason for discount in line_discounts if discount.reason]
        )
        unit_discount_reason = (
            f"{unit_discount_reason} & {promotion_discount_reason}"
            if unit_discount_reason
            else promotion_discount_reason
        )
        line.unit_discount_reason = unit_discount_reason

    is_digital = line.is_digital
    line_info = OrderLineInfo(
        line=line,
        quantity=quantity,
        is_digital=is_digital,
        variant=variant,
        digital_content=variant.digital_content if is_digital and variant else None,
        warehouse_pk=checkout_info.delivery_method_info.warehouse_pk,
        line_discounts=line_discounts,
    )

    return line_info


def _get_unit_discount_reason(
    voucher_code: Optional[str], is_line_voucher_code
) -> Optional[str]:
    if not voucher_code:
        return None
    return (
        f"{'Voucher code' if is_line_voucher_code else 'Entire order voucher code'}: "
        f"{voucher_code}"
    )


def _create_order_line_discounts(
    checkout_line_info: "CheckoutLineInfo", order_line: "OrderLine"
) -> list["OrderLineDiscount"]:
    line_discounts = []
    discounts = checkout_line_info.get_promotion_discounts()
    for discount in discounts:
        discount_data = model_to_dict(discount)
        discount_data.pop("line")
        discount_data["promotion_rule_id"] = discount_data.pop("promotion_rule")
        discount_data["line_id"] = order_line.pk
        line_discounts.append(OrderLineDiscount(**discount_data))
    return line_discounts


def _get_sale_id(line_discounts: list[OrderLineDiscount]):
    for discount in line_discounts:
        if discount.type == DiscountType.PROMOTION:
            if rule := discount.promotion_rule:
                return get_sale_id(rule.promotion)


def _create_lines_for_order(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    prices_entered_with_tax: bool,
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
        check_reservations=True,
    )
    return [
        _create_line_for_order(
            manager,
            checkout_info,
            lines,
            checkout_line_info,
            product_translations,
            variants_translation,
            prices_entered_with_tax,
        )
        for checkout_line_info in lines
    ]


def _prepare_order_data(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    prices_entered_with_tax: bool,
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
    )

    base_shipping_price = base_checkout_delivery_price(checkout_info, lines)
    shipping_total = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )
    shipping_tax_rate = calculations.checkout_shipping_tax_rate(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )
    order_data.update(
        _process_shipping_data_for_order(
            checkout_info, base_shipping_price, shipping_total, manager, lines
        )
    )
    order_data.update(_process_user_data_for_order(checkout_info, manager))

    order_data["lines"] = _create_lines_for_order(
        manager,
        checkout_info,
        lines,
        prices_entered_with_tax,
    )
    undiscounted_total = (
        sum(
            [
                line_data.line.undiscounted_total_price
                for line_data in order_data["lines"]
            ],
            start=zero_taxed_money(taxed_total.currency),
        )
        + shipping_total
    )

    subtotal = get_subtotal(
        [order_line_info.line for order_line_info in order_data["lines"]],
        taxed_total.currency,
    )

    order_data.update(
        {
            "language_code": checkout.language_code,
            "tracking_client_id": checkout.tracking_code or "",
            "total": taxed_total,
            "subtotal": subtotal,
            "undiscounted_total": undiscounted_total,
            "shipping_tax_rate": shipping_tax_rate,
        }
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
        )
        + shipping_total
        - checkout.discount
    ).gross

    try:
        manager.preprocess_order_creation(checkout_info, lines)
    except TaxError:
        _release_checkout_voucher_usage(
            checkout,
            checkout_info.voucher_code,
            checkout_info.voucher,
            order_data.get("user_email"),
        )
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
    site_settings: Optional["SiteSettings"] = None,
    metadata_list: Optional[list] = None,
    private_metadata_list: Optional[list] = None,
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
        if checkout_info.channel.automatically_confirm_all_new_orders
        else OrderStatus.UNCONFIRMED
    )
    order = Order.objects.create(
        **order_data,
        checkout_token=str(checkout.token),
        status=status,
        origin=OrderOrigin.CHECKOUT,
        channel=checkout_info.channel,
        should_refresh_prices=False,
        tax_exemption=checkout_info.checkout.tax_exemption,
    )

    _create_order_discount(order, checkout_info)

    order_lines: list[OrderLine] = []
    order_line_discounts: list[OrderLineDiscount] = []
    for line_info in order_lines_info:
        line = line_info.line
        line.order_id = order.pk
        order_lines.append(line)
        if discounts := line_info.line_discounts:
            order_line_discounts.extend(discounts)

    OrderLine.objects.bulk_create(order_lines)
    OrderLineDiscount.objects.bulk_create(order_line_discounts)

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
        check_reservations=True,
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
    checkout_metadata = get_checkout_metadata(checkout)

    # store current tax configuration
    update_order_display_gross_prices(order)

    # copy metadata from the checkout into the new order
    order.metadata = checkout_metadata.metadata
    if metadata_list:
        order.store_value_in_metadata({data.key: data.value for data in metadata_list})

    order.redirect_url = checkout.redirect_url

    order.private_metadata = checkout_metadata.private_metadata
    if private_metadata_list:
        order.store_value_in_private_metadata(
            {data.key: data.value for data in private_metadata_list}
        )

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
    redirect_url,
):
    """Prepare checkout object to complete the checkout process."""
    checkout = checkout_info.checkout
    clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)
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

    if to_update:
        to_update.append("last_change")
        checkout.save(update_fields=to_update)


def _prepare_checkout_with_transactions(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    redirect_url: Optional[str],
):
    """Prepare checkout object with transactions to complete the checkout process."""
    clean_billing_address(checkout_info, CheckoutErrorCode)
    if (
        checkout_info.checkout.authorize_status != CheckoutAuthorizeStatus.FULL
        and not checkout_info.channel.allow_unpaid_orders
    ):
        raise ValidationError(
            {
                "id": ValidationError(
                    "The authorized amount doesn't cover the checkout's total amount.",
                    code=CheckoutErrorCode.CHECKOUT_NOT_FULLY_PAID.value,
                )
            }
        )
    if checkout_info.checkout.voucher_code and not checkout_info.voucher:
        raise ValidationError(
            {
                "voucher_code": ValidationError(
                    "Voucher not applicable",
                    code=CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.value,
                )
            }
        )
    _validate_gift_cards(checkout_info.checkout)
    _prepare_checkout(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        redirect_url=redirect_url,
    )
    try:
        manager.preprocess_order_creation(checkout_info, lines)
    except TaxError as tax_error:
        raise ValidationError(
            f"Unable to calculate taxes - {str(tax_error)}",
            code=CheckoutErrorCode.TAX_ERROR.value,
        )


def _prepare_checkout_with_payment(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    redirect_url: Optional[str],
    payment: Optional[Payment],
):
    """Prepare checkout object with payment to complete the checkout process."""
    clean_checkout_payment(
        manager,
        checkout_info,
        lines,
        CheckoutErrorCode,
        last_payment=payment,
    )
    _prepare_checkout(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        redirect_url=redirect_url,
    )


def _get_order_data(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    site_settings: "SiteSettings",
) -> dict:
    """Prepare data that will be converted to order and its lines."""
    tax_configuration = checkout_info.tax_configuration
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    try:
        order_data = _prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            prices_entered_with_tax=prices_entered_with_tax,
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
            f"Unable to calculate taxes - {str(tax_error)}",
            code=CheckoutErrorCode.TAX_ERROR.value,
        )
    return order_data


def _process_payment(
    checkout_info: CheckoutInfo,
    payment: Payment,
    customer_id: Optional[str],
    store_source: bool,
    payment_data: Optional[dict],
    manager: "PluginsManager",
    channel_slug: str,
    voucher_code: Optional["VoucherCode"] = None,
    voucher: Optional["Voucher"] = None,
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
        _complete_checkout_fail_handler(checkout_info, manager)
        raise ValidationError(str(e), code=CheckoutErrorCode.PAYMENT_ERROR.value)
    return txn


def complete_checkout_pre_payment_part(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    user,
    site_settings=None,
    redirect_url=None,
) -> tuple[Optional[Payment], Optional[str], dict]:
    """Logic required to process checkout before payment.

    Should be used with transaction_with_commit_on_errors, as there is a possibility
    for thread race.
    :raises ValidationError
    """
    if site_settings is None:
        site_settings = Site.objects.get_current().settings

    fetch_checkout_data(checkout_info, manager, lines)

    checkout = checkout_info.checkout
    payment = checkout.get_last_active_payment()
    try:
        _prepare_checkout_with_payment(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            redirect_url=redirect_url,
            payment=payment,
        )
    except ValidationError as exc:
        _complete_checkout_fail_handler(checkout_info, manager, payment=payment)
        raise exc

    try:
        order_data = _get_order_data(manager, checkout_info, lines, site_settings)
    except ValidationError as exc:
        _complete_checkout_fail_handler(checkout_info, manager, payment=payment)
        raise exc

    customer_id = None
    if payment and user:
        customer_id = fetch_customer_id(user=user, gateway=payment.gateway)

    return payment, customer_id, order_data


def complete_checkout_post_payment_part(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    payment: Optional[Payment],
    txn: Optional[Transaction],
    order_data,
    user,
    app,
    site_settings=None,
    metadata_list: Optional[list] = None,
    private_metadata_list: Optional[list] = None,
) -> tuple[Optional[Order], bool, dict]:
    action_required = False
    action_data: dict[str, str] = {}

    if payment and txn:
        if txn.customer_id and user:
            store_customer_id(user, payment.gateway, txn.customer_id)

        action_required = txn.action_required
        if action_required:
            action_data = txn.action_required_data
            _release_checkout_voucher_usage(
                checkout_info.checkout,
                checkout_info.voucher_code,
                checkout_info.voucher,
                order_data.get("user_email"),
            )

    order = None
    if not action_required and not _is_refund_ongoing(payment):
        try:
            order = _create_order(
                checkout_info=checkout_info,
                checkout_lines=lines,
                order_data=order_data,
                user=user,
                app=app,
                manager=manager,
                site_settings=site_settings,
                metadata_list=metadata_list,
                private_metadata_list=private_metadata_list,
            )
            # remove checkout after order is successfully created
            checkout_info.checkout.delete()
        except InsufficientStock as e:
            _complete_checkout_fail_handler(
                checkout_info,
                manager,
                voucher_code=checkout_info.voucher_code,
                voucher=checkout_info.voucher,
                payment=payment,
            )
            error = prepare_insufficient_stock_checkout_validation_error(e)
            raise error
        except GiftCardNotApplicable as e:
            _complete_checkout_fail_handler(
                checkout_info,
                manager,
                voucher_code=checkout_info.voucher_code,
                voucher=checkout_info.voucher,
                payment=payment,
            )
            raise ValidationError(code=e.code, message=e.message)

        # if the order total value is 0 it is paid from the definition
        if order.total.net.amount == 0:
            if (
                order.channel.order_mark_as_paid_strategy
                == MarkAsPaidStrategy.PAYMENT_FLOW
            ):
                mark_order_as_paid_with_payment(order, user, app, manager)

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


def _increase_voucher_code_usage_value(checkout_info: "CheckoutInfo"):
    """Increase a voucher usage applied to the checkout."""
    voucher, code = get_voucher_for_checkout_info(checkout_info, with_lock=True)
    if not voucher or not code:
        return None

    customer_email = cast(str, checkout_info.get_customer_email())

    checkout = checkout_info.checkout
    _increase_checkout_voucher_usage(checkout, code, voucher, customer_email)
    return code


def _create_order_lines_from_checkout_lines(
    checkout_info: CheckoutInfo,
    lines: list[CheckoutLineInfo],
    manager: "PluginsManager",
    order_pk: Union[str, UUID],
    prices_entered_with_tax: bool,
) -> list[OrderLineInfo]:
    order_lines_info = _create_lines_for_order(
        manager,
        checkout_info,
        lines,
        prices_entered_with_tax,
    )
    order_lines = []
    order_line_discounts: list[OrderLineDiscount] = []
    for line_info in order_lines_info:
        line = line_info.line
        line.order_id = order_pk
        order_lines.append(line)
        if discounts := line_info.line_discounts:
            order_line_discounts.extend(discounts)

    OrderLine.objects.bulk_create(order_lines)
    OrderLineDiscount.objects.bulk_create(order_line_discounts)

    return list(order_lines_info)


def _handle_allocations_of_order_lines(
    checkout_info: CheckoutInfo,
    checkout_lines: list[CheckoutLineInfo],
    order_lines_info: list[OrderLineInfo],
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
        check_reservations=True,
        checkout_lines=[line.line for line in checkout_lines],
    )
    allocate_preorders(
        order_lines_info,
        checkout_info.channel.slug,
        check_reservations=reservation_enabled,
        checkout_lines=[line.line for line in checkout_lines],
    )


def _create_order_discount(order: "Order", checkout_info: "CheckoutInfo"):
    checkout = checkout_info.checkout
    checkout_discount = checkout.discounts.first()
    is_voucher_discount = checkout.discount and not checkout_discount
    is_promotion_discount = (
        checkout_discount and checkout_discount.type == DiscountType.ORDER_PROMOTION
    )

    if is_promotion_discount:
        checkout_discount = cast(CheckoutDiscount, checkout_discount)
        discount_data = model_to_dict(checkout_discount)
        discount_data["promotion_rule"] = checkout_discount.promotion_rule
        del discount_data["checkout"]
        order.discounts.create(**discount_data)

    if is_voucher_discount:
        # Currently, we don't create `CheckoutDiscount` of type VOUCHER, so if there is
        # discount on checkout, but not related `CheckoutDiscount`, we assume it is
        # a voucher discount.
        # Store voucher as a fixed value as it this the simplest solution for now.
        # This will be solved when we refactor the voucher logic to use .discounts
        # relations.
        order.discounts.create(
            type=DiscountType.VOUCHER,
            value_type=DiscountValueType.FIXED,
            value=checkout.discount.amount,
            name=checkout.discount_name,
            translated_name=checkout.translated_discount_name,
            currency=checkout.currency,
            amount_value=checkout.discount_amount,
            voucher=checkout_info.voucher,
            voucher_code=checkout_info.voucher_code.code
            if checkout_info.voucher_code
            else None,
        )


def _post_create_order_actions(
    order: "Order",
    checkout_info: "CheckoutInfo",
    order_lines_info: list["OrderLineInfo"],
    manager: "PluginsManager",
    user: Optional[User],
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
    checkout_lines_info: list[CheckoutLineInfo],
    manager: "PluginsManager",
    user: Optional[User],
    app: Optional["App"],
    metadata_list: Optional[list] = None,
    private_metadata_list: Optional[list] = None,
):
    from ..order.utils import add_gift_cards_to_order

    site_settings = Site.objects.get_current().settings

    address = checkout_info.shipping_address or checkout_info.billing_address

    reservation_enabled = is_reservation_enabled(site_settings)
    tax_configuration = checkout_info.tax_configuration
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax

    # total
    taxed_total = calculations.calculate_checkout_total_with_gift_cards(
        manager=manager,
        checkout_info=checkout_info,
        lines=checkout_lines_info,
        address=address,
    )

    # voucher
    voucher = checkout_info.voucher

    # shipping
    base_shipping_price = base_checkout_delivery_price(
        checkout_info, checkout_lines_info
    )
    shipping_total = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=checkout_lines_info,
        address=address,
    )
    shipping_tax_rate = calculations.checkout_shipping_tax_rate(
        manager=manager,
        checkout_info=checkout_info,
        lines=checkout_lines_info,
        address=address,
    )

    # status
    status = (
        OrderStatus.UNFULFILLED
        if (
            checkout_info.channel.automatically_confirm_all_new_orders
            and checkout_info.checkout.payment_transactions.exists()
        )
        else OrderStatus.UNCONFIRMED
    )
    checkout_metadata = get_or_create_checkout_metadata(checkout_info.checkout)

    # update metadata
    if metadata_list:
        checkout_metadata.store_value_in_metadata(
            {data.key: data.value for data in metadata_list}
        )
    if private_metadata_list:
        checkout_metadata.store_value_in_private_metadata(
            {data.key: data.value for data in private_metadata_list}
        )

    # order
    order = Order.objects.create(  # type: ignore[misc] # see below:
        status=status,
        language_code=checkout_info.checkout.language_code,
        total=taxed_total,  # money field not supported by mypy_django_plugin
        shipping_tax_rate=shipping_tax_rate,
        voucher=voucher,
        checkout_token=str(checkout_info.checkout.token),
        origin=OrderOrigin.CHECKOUT,
        channel=checkout_info.channel,
        metadata=checkout_metadata.metadata,
        private_metadata=checkout_metadata.private_metadata,
        redirect_url=checkout_info.checkout.redirect_url,
        should_refresh_prices=False,
        tax_exemption=checkout_info.checkout.tax_exemption,
        **_process_shipping_data_for_order(
            checkout_info,
            base_shipping_price,
            shipping_total,
            manager,
            checkout_lines_info,
        ),
        **_process_user_data_for_order(checkout_info, manager),
    )

    # checkout discount
    _create_order_discount(order, checkout_info)

    # lines
    order_lines_info = _create_order_lines_from_checkout_lines(
        checkout_info=checkout_info,
        lines=checkout_lines_info,
        manager=manager,
        order_pk=order.pk,
        prices_entered_with_tax=prices_entered_with_tax,
    )

    # update undiscounted order total
    undiscounted_total = (
        sum(
            [line_info.line.undiscounted_total_price for line_info in order_lines_info],
            start=zero_taxed_money(taxed_total.currency),
        )
        + shipping_total
    )
    order.undiscounted_total = undiscounted_total
    currency = checkout_info.checkout.currency
    subtotal_list = [line.line.total_price for line in order_lines_info]
    order.subtotal = sum(subtotal_list, zero_taxed_money(currency))
    order.save(
        update_fields=[
            "undiscounted_total_net_amount",
            "undiscounted_total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
        ]
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
    total_without_giftcard = (
        order.subtotal + shipping_total - checkout_info.checkout.discount
    )
    add_gift_cards_to_order(
        checkout_info, order, total_without_giftcard.gross, user, app
    )

    # payments
    checkout_info.checkout.payments.update(order=order, checkout_id=None)
    checkout_info.checkout.payment_transactions.update(order=order, checkout_id=None)
    update_order_charge_data(order, with_save=False)
    update_order_authorize_data(order, with_save=False)

    # tax settings
    update_order_display_gross_prices(order)

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
    manager: "PluginsManager",
    user: Optional["User"],
    app: Optional["App"],
    delete_checkout: bool = True,
    metadata_list: Optional[list] = None,
    private_metadata_list: Optional[list] = None,
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

    code = None

    if voucher := checkout_info.voucher:
        with transaction.atomic():
            code = _increase_voucher_code_usage_value(checkout_info=checkout_info)

    with transaction.atomic():
        checkout_pk = checkout_info.checkout.pk
        checkout = Checkout.objects.select_for_update().filter(pk=checkout_pk).first()
        if not checkout:
            order = Order.objects.get_by_checkout_token(checkout_pk)
            return order

        # Fetching checkout info inside the transaction block with select_for_update
        # ensure that we are processing checkout on the current data.
        checkout_lines, _ = fetch_checkout_lines(checkout, voucher=voucher)
        checkout_info = fetch_checkout_info(
            checkout, checkout_lines, manager, voucher=voucher, voucher_code=code
        )
        assign_checkout_user(user, checkout_info)

        try:
            order = _create_order_from_checkout(
                checkout_info=checkout_info,
                checkout_lines_info=list(checkout_lines),
                manager=manager,
                user=user,
                app=app,
                metadata_list=metadata_list,
                private_metadata_list=private_metadata_list,
            )
            if delete_checkout:
                checkout_info.checkout.delete()
            return order
        except InsufficientStock:
            _complete_checkout_fail_handler(
                checkout_info,
                manager,
                voucher_code=code,
                voucher=voucher,
            )
            raise
        except GiftCardNotApplicable:
            _complete_checkout_fail_handler(
                checkout_info,
                manager,
                voucher_code=code,
                voucher=voucher,
            )
            raise


def assign_checkout_user(
    user: Optional["User"],
    checkout_info: "CheckoutInfo",
):
    # Assign checkout user to an existing user if checkout email matches a valid
    #  customer account
    if user is None and not checkout_info.user and checkout_info.checkout.email:
        existing_user = retrieve_user_by_email(checkout_info.checkout.email)
        checkout_info.user = (
            existing_user if existing_user and existing_user.is_active else None
        )


def complete_checkout(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    payment_data: dict[Any, Any],
    store_source: bool,
    user: Optional["User"],
    app: Optional["App"],
    site_settings: Optional["SiteSettings"] = None,
    redirect_url: Optional[str] = None,
    metadata_list: Optional[list] = None,
    private_metadata_list: Optional[list] = None,
) -> tuple[Optional[Order], bool, dict]:
    checkout = checkout_info.checkout
    transactions = checkout_info.checkout.payment_transactions.all()

    force_update = checkout_info.checkout.tax_error is not None
    fetch_checkout_data(
        checkout_info,
        manager,
        lines,
        force_update=force_update,
    )
    if checkout_info.checkout.tax_error is not None:
        raise ValidationError(
            "Configured Tax App didn't responded.",
            code=CheckoutErrorCode.TAX_ERROR.value,
        )

    active_payment = checkout.get_last_active_payment()
    is_checkout_fully_authorized = (
        checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    )
    checkout_is_zero = checkout_info.checkout.total.gross.amount == Decimal(0)
    is_transaction_flow = (
        checkout_info.channel.order_mark_as_paid_strategy
        == MarkAsPaidStrategy.TRANSACTION_FLOW
    )
    # When checkout is zero, we don't need any transaction to cover the checkout total.
    # We check if checkout is zero, and we also check what flow for marking an order as
    # paid is used. In case when we have TRANSACTION_FLOW we use transaction flow to
    # finalize the checkout.
    # When checkout is not fully authorized and contains active payment, we use the
    # payment flow to finalize the checkout.
    if (
        is_checkout_fully_authorized
        or (transactions and not active_payment)
        or checkout_info.channel.allow_unpaid_orders
        or (checkout_is_zero and is_transaction_flow)
    ):
        order = complete_checkout_with_transaction(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            user=user,
            app=app,
            redirect_url=redirect_url,
            metadata_list=metadata_list,
            private_metadata_list=private_metadata_list,
        )
        return order, False, {}

    return complete_checkout_with_payment(
        manager=manager,
        checkout_pk=checkout_info.checkout.pk,
        payment_data=payment_data,
        store_source=store_source,
        user=user,
        app=app,
        site_settings=site_settings,
        redirect_url=redirect_url,
        metadata_list=metadata_list,
        private_metadata_list=private_metadata_list,
    )


def complete_checkout_with_transaction(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    user: Optional["User"],
    app: Optional["App"],
    redirect_url: Optional[str] = None,
    metadata_list: Optional[list] = None,
    private_metadata_list: Optional[list] = None,
) -> Optional[Order]:
    try:
        _prepare_checkout_with_transactions(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            redirect_url=redirect_url,
        )

        return create_order_from_checkout(
            checkout_info=checkout_info,
            manager=manager,
            user=user,
            app=app,
            delete_checkout=True,
            metadata_list=metadata_list,
            private_metadata_list=private_metadata_list,
        )
    except NotApplicable:
        raise ValidationError(
            {
                "voucher_code": ValidationError(
                    "Voucher not applicable",
                    code=CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.value,
                )
            }
        )
    except InsufficientStock as e:
        error = prepare_insufficient_stock_checkout_validation_error(e)
        raise error
    except GiftCardNotApplicable as e:
        raise ValidationError({"gift_cards": e})


def complete_checkout_with_payment(
    manager: "PluginsManager",
    checkout_pk: UUID,
    payment_data,
    store_source,
    user,
    app,
    site_settings=None,
    redirect_url=None,
    metadata_list: Optional[list] = None,
    private_metadata_list: Optional[list] = None,
) -> tuple[Optional[Order], bool, dict]:
    """Logic required to finalize the checkout and convert it to order.

    Should be used with transaction_with_commit_on_errors, as there is a possibility
    for thread race.
    :raises ValidationError
    """
    with transaction_with_commit_on_errors():
        checkout = Checkout.objects.select_for_update().filter(pk=checkout_pk).first()
        if not checkout:
            order = Order.objects.get_by_checkout_token(checkout_pk)
            return order, False, {}

        checkout.completing_started_at = timezone.now()
        checkout.save(update_fields=["completing_started_at"])

        # Fetching checkout info inside the transaction block with select_for_update
        # enure that we are processing checkout on the current data.
        lines, _ = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(checkout, lines, manager)
        assign_checkout_user(user, checkout_info)

        payment, customer_id, order_data = complete_checkout_pre_payment_part(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            user=user,
            site_settings=site_settings,
            redirect_url=redirect_url,
        )

        _reserve_stocks_without_availability_check(checkout_info, lines)

    # Process payments out of transaction to unlock stock rows for another user,
    # who potentially can order the same product variants.
    txn = None
    channel_slug = checkout_info.channel.slug
    voucher = checkout_info.voucher
    voucher_code = checkout_info.voucher_code
    if payment:
        with transaction_with_commit_on_errors():
            checkout = (
                Checkout.objects.select_for_update().filter(pk=checkout_pk).first()
            )

            if not checkout:
                order = Order.objects.get_by_checkout_token(checkout_pk)
                return order, False, {}

            payment = Payment.objects.select_for_update().get(id=payment.id)
            txn = _process_payment(
                checkout_info=checkout_info,
                payment=payment,
                customer_id=customer_id,
                store_source=store_source,
                payment_data=payment_data,
                manager=manager,
                channel_slug=channel_slug,
                voucher_code=checkout_info.voucher_code,
                voucher=checkout_info.voucher,
            )

            # As payment processing might take a while, we need to check if the payment
            # doesn't become inactive in the meantime. If it's inactive we need to
            # refund the payment.
            payment.refresh_from_db()
            if not payment.is_active:
                _complete_checkout_fail_handler(
                    checkout_info,
                    manager,
                    voucher=order_data.get("voucher"),
                    payment=payment,
                )
                raise ValidationError(
                    f"The payment with pspReference: {payment.psp_reference} is "
                    "inactive.",
                    code=CheckoutErrorCode.INACTIVE_PAYMENT.value,
                )

    with transaction_with_commit_on_errors():
        checkout = (
            Checkout.objects.select_for_update()
            .filter(pk=checkout_info.checkout.pk)
            .first()
        )
        if not checkout:
            order = Order.objects.get_by_checkout_token(checkout_info.checkout.token)
            return order, False, {}

        # We need to refetch the checkout info to ensure that we process checkout
        # for correct data.
        lines, _ = fetch_checkout_lines(checkout, skip_recalculation=True)

        # reassign voucher data that was used during payment process to allow voucher
        # usage releasing in case of checkout complete failure
        checkout_info = fetch_checkout_info(
            checkout, lines, manager, voucher=voucher, voucher_code=voucher_code
        )

        order, action_required, action_data = complete_checkout_post_payment_part(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            payment=payment,
            txn=txn,
            order_data=order_data,
            user=user,
            app=app,
            site_settings=site_settings,
            metadata_list=metadata_list,
            private_metadata_list=private_metadata_list,
        )
        if checkout.pk:
            checkout.completing_started_at = None
            checkout.save(update_fields=["completing_started_at"])

    return order, action_required, action_data


def _reserve_stocks_without_availability_check(
    checkout_info: CheckoutInfo,
    lines: Iterable[CheckoutLineInfo],
):
    """Add additional temporary reservation for stock.

    Due to unlocking rows, for the time of external payment call, it prevents users
    ordering the same product, in the same time, which is out of stock.
    """
    variants = [line.variant for line in lines]
    stocks = Stock.objects.get_variants_stocks_for_country(
        country_code=checkout_info.get_country(),
        channel_slug=checkout_info.channel.slug,
        products_variants=variants,
    )
    variants_stocks_map = {stock.product_variant_id: stock for stock in stocks}

    reservations = []
    for line in lines:
        if line.variant.id in variants_stocks_map:
            reservations.append(
                Reservation(
                    quantity_reserved=line.line.quantity,
                    reserved_until=timezone.now()
                    + timedelta(seconds=settings.RESERVE_DURATION),
                    stock=variants_stocks_map[line.variant.id],
                    checkout_line=line.line,
                )
            )
    Reservation.objects.bulk_create(reservations)
    return reservations


def _complete_checkout_fail_handler(
    checkout_info: "CheckoutInfo",
    manager: "PluginsManager",
    *,
    voucher_code: Optional["VoucherCode"] = None,
    voucher: Optional["Voucher"] = None,
    payment: Optional[Payment] = None,
) -> None:
    """Handle the case when the checkout completion failed.

    - Release the checkout processing indicator.
    - Release the voucher usage.
    - Refund or void the payment.
    """
    checkout = checkout_info.checkout
    update_fields = []
    if checkout.completing_started_at is not None:
        # release the checkout processing indicator
        checkout.completing_started_at = None
        update_fields.append("completing_started_at")

    # release the voucher usage
    if voucher:
        _release_checkout_voucher_usage(
            checkout,
            voucher_code,
            voucher,
            checkout.get_customer_email(),
            update_fields,
        )

    if update_fields:
        checkout.save(update_fields=update_fields)

    if payment:
        gateway.payment_refund_or_void(
            payment, manager, channel_slug=checkout_info.channel.slug
        )
