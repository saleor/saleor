import json
from decimal import Decimal
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import graphene
from prices import TaxedMoney

from ..checkout import calculations as checkout_calculations
from ..checkout.fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ..checkout.models import Checkout
from ..core.prices import quantize_price_fields
from ..core.taxes import include_taxes_in_prices
from ..order import calculations as order_calculations
from ..order.models import Order, OrderLine
from ..plugins.base_plugin import RequestorOrLazyObject
from ..plugins.manager import PluginsManager, get_plugins_manager
from ..warehouse.models import Warehouse
from . import traced_payload_generator
from .payload_serializers import PayloadSerializer
from .payloads_utils import (
    ADDRESS_FIELDS,
    charge_taxes,
    generate_collection_point_payload,
    generate_fulfillment_lines_payload,
    generate_meta,
    generate_requestor,
    get_product_metadata_for_order_line,
    get_product_type_metadata_for_order_line,
    prepare_order_lines_allocations_payload,
    quantize_lazy_prices,
    quantize_prices,
)
from .serializers import serialize_checkout_lines

ORDER_LINE_FIELDS_WITH_TAXES = (
    "product_name",
    "variant_name",
    "translated_product_name",
    "translated_variant_name",
    "product_sku",
    "quantity",
    "currency",
    "unit_discount_amount",
    "unit_discount_type",
    "unit_discount_reason",
    "tax_rate",
    "sale_id",
    "voucher_code",
)


ORDER_LINE_FIELDS_WITHOUT_TAXES = (
    "product_name",
    "variant_name",
    "translated_product_name",
    "translated_variant_name",
    "product_sku",
    "quantity",
    "currency",
    "unit_discount_amount",
    "unit_discount_type",
    "unit_discount_reason",
    "unit_price_net_amount",
    "unit_price_gross_amount",
    "total_price_net_amount",
    "total_price_gross_amount",
    "undiscounted_unit_price_net_amount",
    "undiscounted_unit_price_gross_amount",
    "undiscounted_total_price_net_amount",
    "undiscounted_total_price_gross_amount",
    "sale_id",
    "voucher_code",
)


ORDER_LINE_PRICE_FIELDS = (
    "unit_discount_amount",
    "unit_price_net_amount",
    "unit_price_gross_amount",
    "total_price_net_amount",
    "total_price_gross_amount",
    "undiscounted_unit_price_net_amount",
    "undiscounted_unit_price_gross_amount",
    "undiscounted_total_price_net_amount",
    "undiscounted_total_price_gross_amount",
)


@quantize_lazy_prices
def _generate_order_line_prices_data(
    order: "Order",
    manager: PluginsManager,
    lines: Iterable[OrderLine],
) -> Dict[str, Callable[[OrderLine], Decimal]]:
    def get_unit_price(line: OrderLine) -> TaxedMoney:
        return order_calculations.order_line_unit(
            order, line, manager, lines
        ).price_with_discounts

    def get_undiscounted_unit_price(line: OrderLine) -> TaxedMoney:
        return order_calculations.order_line_unit(
            order, line, manager, lines
        ).undiscounted_price

    def get_total_price(line: OrderLine) -> TaxedMoney:
        return order_calculations.order_line_total(
            order, line, manager, lines
        ).price_with_discounts

    def get_undiscounted_total_price(line: OrderLine) -> TaxedMoney:
        return order_calculations.order_line_total(
            order, line, manager, lines
        ).undiscounted_price

    return {
        "unit_price_net_amount": (lambda l: get_unit_price(l).net.amount),
        "unit_price_gross_amount": (lambda l: get_unit_price(l).gross.amount),
        "total_price_net_amount": (lambda l: get_total_price(l).net.amount),
        "total_price_gross_amount": (lambda l: get_total_price(l).gross.amount),
        "undiscounted_unit_price_net_amount": (
            lambda l: get_undiscounted_unit_price(l).net.amount
        ),
        "undiscounted_unit_price_gross_amount": (
            lambda l: get_undiscounted_unit_price(l).gross.amount
        ),
        "undiscounted_total_price_net_amount": (
            lambda l: get_undiscounted_total_price(l).net.amount
        ),
        "undiscounted_total_price_gross_amount": (
            lambda l: get_undiscounted_total_price(l).gross.amount
        ),
    }


@traced_payload_generator
def _generate_order_lines_payload(
    lines: Iterable[OrderLine],
    fields: Tuple[str, ...],
    extra_data: Optional[Dict[str, Callable[[OrderLine], Decimal]]] = None,
):
    for line in lines:
        quantize_price_fields(line, ORDER_LINE_PRICE_FIELDS, line.currency)

    serializer = PayloadSerializer()
    return serializer.serialize(
        lines,
        fields=fields,
        extra_dict_data={
            "id": (lambda l: graphene.Node.to_global_id("OrderLine", l.pk)),
            "product_variant_id": (lambda l: l.product_variant_id),
            "allocations": (lambda l: prepare_order_lines_allocations_payload(l)),
            "charge_taxes": (lambda l: charge_taxes(l)),
            "product_metadata": (lambda l: get_product_metadata_for_order_line(l)),
            "product_type_metadata": (
                lambda l: get_product_type_metadata_for_order_line(l)
            ),
            **(extra_data or {}),
        },
    )


ORDER_FIELDS_WITH_TAXES = (
    "token",
    "created",
    "status",
    "origin",
    "user_email",
    "shipping_method_name",
    "collection_point_name",
    "weight",
    "private_metadata",
    "metadata",
)


ORDER_FIELDS_WITHOUT_TAXES = (
    "token",
    "created",
    "status",
    "origin",
    "user_email",
    "shipping_method_name",
    "collection_point_name",
    "weight",
    "shipping_price_net_amount",
    "shipping_price_gross_amount",
    "shipping_tax_rate",
    "total_net_amount",
    "total_gross_amount",
    "undiscounted_total_net_amount",
    "undiscounted_total_gross_amount",
    "private_metadata",
    "metadata",
)


ORDER_PRICE_FIELDS = (
    "shipping_price_net_amount",
    "shipping_price_gross_amount",
    "total_net_amount",
    "total_gross_amount",
    "undiscounted_total_net_amount",
    "undiscounted_total_gross_amount",
)


@quantize_prices
def _generate_order_prices_data(
    order: "Order",
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
) -> Dict[str, Decimal]:

    shipping = order_calculations.order_shipping(order, manager, lines)
    shipping_tax_rate = order_calculations.order_shipping_tax_rate(
        order, manager, lines
    )
    total = order_calculations.order_total(order, manager, lines)
    undiscounted_total = order_calculations.order_undiscounted_total(
        order, manager, lines
    )

    return {
        "shipping_price_net_amount": shipping.net.amount,
        "shipping_price_gross_amount": shipping.gross.amount,
        "shipping_tax_rate": shipping_tax_rate,
        "total_net_amount": total.net.amount,
        "total_gross_amount": total.gross.amount,
        "undiscounted_total_net_amount": undiscounted_total.net.amount,
        "undiscounted_total_gross_amount": undiscounted_total.gross.amount,
    }


@traced_payload_generator
def _generate_order_payload(
    order: "Order",
    requestor: Optional["RequestorOrLazyObject"] = None,
    with_meta: bool = True,
    *,
    fields: Tuple[str, ...],
    serialized_lines: str,
    extra_data: Optional[Dict[str, Decimal]] = None,
):
    serializer = PayloadSerializer()
    fulfillment_fields = (
        "status",
        "tracking_number",
        "created",
        "shipping_refund_amount",
        "total_refund_amount",
    )
    fulfillment_price_fields = ("shipping_refund_amount", "total_refund_amount")
    payment_fields = (
        "gateway",
        "payment_method_type",
        "cc_brand",
        "is_active",
        "created",
        "partial",
        "modified",
        "charge_status",
        "psp_reference",
        "total",
        "captured_amount",
        "currency",
        "billing_email",
        "billing_first_name",
        "billing_last_name",
        "billing_company_name",
        "billing_address_1",
        "billing_address_2",
        "billing_city",
        "billing_city_area",
        "billing_postal_code",
        "billing_country_code",
        "billing_country_area",
    )
    payment_price_fields = ("captured_amount", "total")
    discount_fields = (
        "type",
        "value_type",
        "value",
        "amount_value",
        "name",
        "translated_name",
        "reason",
    )
    discount_price_fields = ("amount_value",)

    channel_fields = ("slug", "currency_code")
    shipping_method_fields = ("name", "type", "currency", "price_amount")

    fulfillments = order.fulfillments.all()
    payments = order.payments.all()
    discounts = order.discounts.all()

    quantize_price_fields(order, ORDER_PRICE_FIELDS, order.currency)

    for fulfillment in fulfillments:
        quantize_price_fields(fulfillment, fulfillment_price_fields, order.currency)

    for payment in payments:
        quantize_price_fields(payment, payment_price_fields, order.currency)

    for discount in discounts:
        quantize_price_fields(discount, discount_price_fields, order.currency)

    fulfillments_data = serializer.serialize(
        fulfillments,
        fields=fulfillment_fields,
        extra_dict_data={
            "lines": lambda f: json.loads(generate_fulfillment_lines_payload(f))
        },
    )

    extra_dict_data = {
        "original": graphene.Node.to_global_id("Order", order.original_id),
        "lines": json.loads(serialized_lines),
        "included_taxes_in_prices": include_taxes_in_prices(),
        "fulfillments": json.loads(fulfillments_data),
        "collection_point": json.loads(
            generate_collection_point_payload(order.collection_point)
        )[0]
        if order.collection_point
        else None,
    }

    if extra_data:
        extra_dict_data.update(extra_data)

    if with_meta:
        extra_dict_data["meta"] = generate_meta(
            requestor_data=generate_requestor(requestor)
        )

    order_data = serializer.serialize(
        [order],
        fields=fields,
        additional_fields={
            "channel": (lambda o: o.channel, channel_fields),
            "shipping_method": (lambda o: o.shipping_method, shipping_method_fields),
            "payments": (lambda _: payments, payment_fields),
            "shipping_address": (lambda o: o.shipping_address, ADDRESS_FIELDS),
            "billing_address": (lambda o: o.billing_address, ADDRESS_FIELDS),
            "discounts": (lambda _: discounts, discount_fields),
        },
        extra_dict_data=extra_dict_data,
    )
    return order_data


def generate_order_payload(
    order: "Order",
    requestor: Optional["RequestorOrLazyObject"] = None,
    with_meta: bool = True,
    taxed: bool = True,
):
    manager = get_plugins_manager()
    lines = OrderLine.objects.prefetch_related("variant__product__product_type")

    if taxed:
        return _generate_order_payload(
            order,
            requestor,
            with_meta,
            fields=ORDER_FIELDS_WITH_TAXES,
            serialized_lines=_generate_order_lines_payload(
                lines=lines,
                fields=ORDER_LINE_FIELDS_WITH_TAXES,
                extra_data=_generate_order_line_prices_data(order, manager, lines),
            ),
            extra_data=_generate_order_prices_data(order, manager, lines),
        )

    return _generate_order_payload(
        order,
        requestor,
        with_meta,
        fields=ORDER_FIELDS_WITHOUT_TAXES,
        serialized_lines=_generate_order_lines_payload(
            lines=lines,
            fields=ORDER_LINE_FIELDS_WITHOUT_TAXES,
        ),
    )


CHECKOUT_FIELDS_WITHOUT_TAXES = (
    "created",
    "last_change",
    "status",
    "email",
    "quantity",
    "currency",
    "subtotal_net_amount",
    "subtotal_gross_amount",
    "total_net_amount",
    "total_gross_amount",
    "discount_amount",
    "discount_name",
    "private_metadata",
    "metadata",
    "channel",
)

CHECKOUT_FIELDS_WITH_TAXES = (
    "created",
    "last_change",
    "status",
    "email",
    "quantity",
    "currency",
    "discount_amount",
    "discount_name",
    "private_metadata",
    "metadata",
    "channel",
)


def _generate_checkout_prices_data(
    manager: PluginsManager,
    checkout_info: CheckoutInfo,
    lines: Iterable[CheckoutLineInfo],
) -> Dict[str, Decimal]:
    subtotal = checkout_calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=None,
    )
    total = checkout_calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=None,
    )

    return {
        "subtotal_net_amount": subtotal.net.amount,
        "subtotal_gross_amount": subtotal.gross.amount,
        "total_net_amount": total.net.amount,
        "total_gross_amount": total.gross.amount,
    }


@traced_payload_generator
def _generate_checkout_payload(
    checkout: "Checkout",
    requestor: Optional["RequestorOrLazyObject"] = None,
    *,
    fields: Tuple[str, ...],
    lines_dict_data: List[dict],
    extra_data: Optional[Dict[str, Decimal]] = None,
):
    serializer = PayloadSerializer()

    checkout_price_fields = (
        "subtotal_net_amount",
        "subtotal_gross_amount",
        "total_net_amount",
        "total_gross_amount",
        "discount_amount",
    )
    quantize_price_fields(checkout, checkout_price_fields, checkout.currency)
    user_fields = ("email", "first_name", "last_name")
    channel_fields = ("slug", "currency_code")
    shipping_method_fields = ("name", "type", "currency", "price_amount")

    # todo use the most appropriate warehouse
    warehouse = None
    if checkout.shipping_address:
        warehouse = Warehouse.objects.for_country(
            checkout.shipping_address.country.code
        ).first()

    checkout_data = serializer.serialize(
        [checkout],
        fields=fields,
        obj_id_name="token",
        additional_fields={
            "channel": (lambda o: o.channel, channel_fields),
            "user": (lambda c: c.user, user_fields),
            "billing_address": (lambda c: c.billing_address, ADDRESS_FIELDS),
            "shipping_address": (lambda c: c.shipping_address, ADDRESS_FIELDS),
            "shipping_method": (lambda c: c.shipping_method, shipping_method_fields),
            "warehouse_address": (
                lambda c: warehouse.address if warehouse else None,
                ADDRESS_FIELDS,
            ),
        },
        extra_dict_data={
            # Casting to list to make it json-serializable
            "included_taxes_in_price": include_taxes_in_prices(),
            "lines": lines_dict_data,
            "collection_point": json.loads(
                generate_collection_point_payload(checkout.collection_point)
            )[0]
            if checkout.collection_point
            else None,
            "meta": generate_meta(requestor_data=generate_requestor(requestor)),
            **(extra_data or {}),
        },
    )
    return checkout_data


def generate_checkout_payload(
    checkout: "Checkout",
    requestor: Optional["RequestorOrLazyObject"] = None,
    taxed: bool = True,
):
    lines, _ = fetch_checkout_lines(checkout, prefetch_variant_attributes=True)

    if not taxed:
        return _generate_checkout_payload(
            checkout,
            requestor,
            fields=CHECKOUT_FIELDS_WITHOUT_TAXES,
            lines_dict_data=serialize_checkout_lines(
                checkout, lines, lambda line_info: line_info.line.unit_price
            ),
        )

    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    def get_unit_price(line_info: CheckoutLineInfo) -> TaxedMoney:
        return checkout_calculations.checkout_line_unit_price(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            checkout_line_info=line_info,
            discounts=[],
        ).price_with_discounts

    return _generate_checkout_payload(
        checkout,
        requestor,
        fields=CHECKOUT_FIELDS_WITH_TAXES,
        lines_dict_data=serialize_checkout_lines(checkout, lines, get_unit_price),
        extra_data=_generate_checkout_prices_data(manager, checkout_info, lines),
    )
