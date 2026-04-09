import logging
from typing import TYPE_CHECKING, Any, Union

import graphene
from promise import Promise

from ...app.models import App
from ...core.db.connection import allow_writer
from ...core.prices import quantize_price
from ...core.taxes import TaxData
from ...discount.utils.voucher import is_order_level_voucher
from ...tax.utils import get_charge_taxes_for_checkout
from ...tax.webhooks import shared
from ...webhook import traced_payload_generator
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.payload_serializers import PayloadSerializer
from ...webhook.serializers import (
    serialize_variant_full_name,
)
from .. import base_calculations
from ..utils import get_checkout_metadata

if TYPE_CHECKING:
    from ...account.models import User
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo

logger = logging.getLogger(__name__)

ADDRESS_FIELDS = (
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
CHANNEL_FIELDS = ("slug", "currency_code")


def _get_checkout_line_payload_data(line_info: "CheckoutLineInfo") -> dict[str, Any]:
    line_id = graphene.Node.to_global_id("CheckoutLine", line_info.line.pk)
    variant = line_info.variant
    product = line_info.product
    return {
        "id": line_id,
        "sku": variant.sku,
        "variant_id": variant.get_global_id(),
        "quantity": line_info.line.quantity,
        "full_name": serialize_variant_full_name(variant, product=product),
        "product_name": product.name,
        "variant_name": variant.name,
        "product_metadata": line_info.product.metadata,
        "product_type_metadata": line_info.product_type.metadata,
    }


def serialize_checkout_lines_for_tax_calculation(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
) -> list[dict]:
    charge_taxes = get_charge_taxes_for_checkout(checkout_info)
    return [
        {
            **_get_checkout_line_payload_data(line_info),
            "charge_taxes": charge_taxes,
            "unit_amount": quantize_price(
                base_calculations.calculate_base_line_unit_price(line_info).amount,
                checkout_info.checkout.currency,
            ),
            "total_amount": quantize_price(
                base_calculations.calculate_base_line_total_price(line_info).amount,
                checkout_info.checkout.currency,
            ),
        }
        for line_info in lines
    ]


@allow_writer()
@traced_payload_generator
def generate_checkout_payload_for_tax_calculation(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
):
    checkout = checkout_info.checkout
    tax_configuration = checkout_info.tax_configuration
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax

    serializer = PayloadSerializer()

    checkout_fields = ("currency",)

    # Prepare checkout data
    address = checkout_info.shipping_address or checkout_info.billing_address

    total_amount = quantize_price(
        base_calculations.base_checkout_total(checkout_info, lines).amount,
        checkout.currency,
    )

    # Prepare user data
    user = checkout_info.user
    user_id = None
    user_public_metadata = {}
    if user:
        user_id = graphene.Node.to_global_id("User", user.id)
        user_public_metadata = user.metadata

    # order promotion discount and entire_order voucher discount with
    # apply_once_per_order set to False is not already included in the total price
    discounted_object_promotion = bool(checkout_info.discounts)
    discount_not_included = discounted_object_promotion or is_order_level_voucher(
        checkout_info.voucher
    )
    if not checkout.discount_amount:
        discounts = []
    else:
        discount_amount = quantize_price(checkout.discount_amount, checkout.currency)
        discount_name = checkout.discount_name
        discounts = (
            [{"name": discount_name, "amount": discount_amount}]
            if discount_amount and discount_not_included
            else []
        )

    # Prepare shipping data
    assigned_delivery = checkout.assigned_delivery
    shipping_method_name = None
    if assigned_delivery:
        shipping_method_name = assigned_delivery.name
    shipping_method_amount = quantize_price(
        base_calculations.base_checkout_delivery_price(checkout_info, lines).amount,
        checkout.currency,
    )

    # Prepare line data
    lines_dict_data = serialize_checkout_lines_for_tax_calculation(checkout_info, lines)

    checkout_data = serializer.serialize(
        [checkout],
        fields=checkout_fields,
        pk_field_name="token",
        additional_fields={
            "channel": (lambda c: c.channel, CHANNEL_FIELDS),
            "address": (lambda _: address, ADDRESS_FIELDS),
        },
        extra_dict_data={
            "user_id": user_id,
            "user_public_metadata": user_public_metadata,
            "included_taxes_in_prices": prices_entered_with_tax,
            "total_amount": total_amount,
            "shipping_amount": shipping_method_amount,
            "shipping_name": shipping_method_name,
            "discounts": discounts,
            "lines": lines_dict_data,
            "metadata": (
                lambda c=checkout: (
                    get_checkout_metadata(c).metadata  # type: ignore[union-attr]
                    if hasattr(c, "metadata_storage")
                    else {}
                )
            ),
        },
    )
    return checkout_data


def get_taxes(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    app_identifier: str | None,
    requestor: Union["App", "User", None] = None,
) -> Promise[TaxData | None]:
    return shared.get_taxes(
        taxable_object=checkout_info.checkout,
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        app_identifier=app_identifier,
        static_payload=generate_checkout_payload_for_tax_calculation(
            checkout_info, lines
        ),
        lines_count=len(lines),
        requestor=requestor,
    )
