import logging
from typing import TYPE_CHECKING, Union

import graphene
from django.conf import settings

from ...app.models import App
from ...core.db.connection import allow_writer
from ...core.prices import quantize_price
from ...core.taxes import TaxData, TaxDataError
from ...discount.utils.voucher import is_order_level_voucher
from ...graphql.webhook.subscription_payload import initialize_request
from ...graphql.webhook.utils import get_pregenerated_subscription_payload
from ...tax.webhooks.parser import parse_tax_data
from ...webhook import traced_payload_generator
from ...webhook.event_types import WebhookEventSyncType
from ...webhook.payload_serializers import PayloadSerializer
from ...webhook.serializers import serialize_checkout_lines_for_tax_calculation
from ...webhook.transport.synchronous.transport import (
    trigger_taxes_all_webhooks_sync,
    trigger_webhook_sync,
)
from ...webhook.utils import get_webhooks_for_event
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


def trigger_tax_webhook(
    app_identifier: str,
    payload: str,
    expected_lines_count: int,
    subscriptable_object=None,
    requestor: Union["App", "User", None] = None,
    pregenerated_subscription_payloads: dict | None = None,
) -> TaxData:
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES

    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    app = (
        App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(
            identifier=app_identifier,
            is_active=True,
        )
        .order_by("-created_at")
        .first()
    )
    if app is None:
        msg = "Configured tax app doesn't exist."
        logger.warning(msg)
        raise TaxDataError(msg)
    webhook = get_webhooks_for_event(event_type, apps_ids=[app.id]).first()
    if webhook is None:
        msg = "Configured tax app's webhook for taxes calculation doesn't exists."
        logger.warning(msg)
        raise TaxDataError(msg)

    request_context = initialize_request(
        app=app,
        requestor=requestor,
        sync_event=event_type in WebhookEventSyncType.ALL,
        allow_replica=False,
        event_type=event_type,
    )

    pregenerated_subscription_payload = get_pregenerated_subscription_payload(
        webhook, pregenerated_subscription_payloads
    )
    response = trigger_webhook_sync(
        event_type=event_type,
        webhook=webhook,
        payload=payload,
        allow_replica=False,
        subscribable_object=subscriptable_object,
        request=request_context,
        requestor=requestor,
        pregenerated_subscription_payload=pregenerated_subscription_payload,
    )
    return parse_tax_data(event_type, response, expected_lines_count)


def get_taxes(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    app_identifier: str | None,
    requestor: Union["App", "User", None] = None,
    pregenerated_subscription_payloads: dict | None = None,
) -> TaxData | None:
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    lines_count = len(lines)
    if app_identifier:
        return trigger_tax_webhook(
            app_identifier=app_identifier,
            payload=generate_checkout_payload_for_tax_calculation(checkout_info, lines),
            expected_lines_count=lines_count,
            subscriptable_object=checkout_info.checkout,
            pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        )

    # This is deprecated flow, kept to maintain backward compatibility.
    # In Saleor 4.0 `tax_app_identifier` should be required and the flow should
    # be dropped.
    return trigger_taxes_all_webhooks_sync(
        event_type,
        lambda: generate_checkout_payload_for_tax_calculation(
            checkout_info,
            lines,
        ),
        lines_count,
        checkout_info.checkout,
        requestor,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
    )
