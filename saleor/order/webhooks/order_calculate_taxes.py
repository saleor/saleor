import json
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Union

import graphene
from django.db.models import QuerySet
from promise import Promise

from ...app.models import App
from ...core.db.connection import allow_writer
from ...core.prices import quantize_price, quantize_price_fields
from ...core.taxes import TaxData
from ...discount.utils.shared import is_order_level_discount
from ...tax.utils import get_charge_taxes_for_order
from ...tax.webhooks import shared
from ...webhook import traced_payload_generator
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.payload_serializers import PayloadSerializer
from ..models import Order, OrderLine

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App


logger = logging.getLogger(__name__)


def _generate_order_lines_payload_for_tax_calculation(lines: QuerySet[OrderLine]):
    serializer = PayloadSerializer()

    charge_taxes = False
    if lines:
        charge_taxes = get_charge_taxes_for_order(lines[0].order)

    return serializer.serialize(
        lines,
        fields=("product_name", "variant_name", "quantity"),
        extra_dict_data={
            "variant_id": (lambda line: line.product_variant_id),
            "full_name": (
                lambda line: line.variant.display_product() if line.variant else None
            ),
            "product_metadata": (
                lambda line: line.variant.product.metadata if line.variant else {}
            ),
            "product_type_metadata": (
                lambda line: (
                    line.variant.product.product_type.metadata if line.variant else {}
                )
            ),
            "charge_taxes": (lambda _line: charge_taxes),
            "sku": (lambda line: line.product_sku),
            "unit_amount": (
                lambda line: quantize_price(line.base_unit_price_amount, line.currency)
            ),
            "total_amount": (
                lambda line: quantize_price(
                    line.base_unit_price_amount * line.quantity, line.currency
                )
            ),
        },
    )


@allow_writer()
@traced_payload_generator
def generate_order_payload_for_tax_calculation(order: "Order"):
    serializer = PayloadSerializer()

    tax_configuration = order.channel.tax_configuration
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax

    # Prepare Order data
    address = order.shipping_address or order.billing_address
    lines = order.lines.all()

    # Prepare user data
    user = order.user
    user_id = None
    user_public_metadata = {}
    if user:
        user_id = graphene.Node.to_global_id("User", user.id)
        user_public_metadata = user.metadata

    # Prepare discount data
    discounts = order.discounts.all()
    discounts_dict = []
    for discount in discounts:
        # Only order level discounts, like entire order vouchers,
        # order promotions and manual discounts should be taken into account
        if not is_order_level_discount(discount):
            continue
        quantize_price_fields(discount, ("amount_value",), order.currency)
        discount_amount = quantize_price(discount.amount_value, order.currency)
        discounts_dict.append({"name": discount.name, "amount": discount_amount})

    # Prepare shipping data
    shipping_method_name = order.shipping_method_name
    shipping_method_amount = quantize_price(
        order.base_shipping_price_amount, order.currency
    )

    address_fields = (
        "first_name",
        "last_name",
        "company_name",
        "street_address_1",
        "street_address_2",
        "city",
        "city_area",
        "postal_code",
        "country",
        "country_area",
        "phone",
    )
    order_data = serializer.serialize(
        [order],
        fields=["currency", "metadata"],
        additional_fields={
            "channel": (lambda o: o.channel, ("slug", "currency_code")),
            "address": (lambda o: address, address_fields),
        },
        extra_dict_data={
            "id": graphene.Node.to_global_id("Order", order.id),
            "user_id": user_id,
            "user_public_metadata": user_public_metadata,
            "discounts": discounts_dict,
            "included_taxes_in_prices": prices_entered_with_tax,
            "shipping_amount": shipping_method_amount,
            "shipping_name": shipping_method_name,
            "lines": json.loads(
                _generate_order_lines_payload_for_tax_calculation(lines)
            ),
        },
    )
    return order_data


def get_taxes(
    order: Order,
    lines: Iterable["OrderLine"],
    app_identifier: str | None,
    requestor: Union["App", "User", None],
) -> Promise[TaxData | None]:
    return shared.get_taxes(
        taxable_object=order,
        event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES,
        app_identifier=app_identifier,
        static_payload=generate_order_payload_for_tax_calculation(order),
        lines_count=len(list(lines)),
        requestor=requestor,
    )
