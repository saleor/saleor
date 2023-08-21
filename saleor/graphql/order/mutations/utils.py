from collections import namedtuple
from typing import Optional

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError

from ....checkout.fetch import get_variant_channel_listing
from ....core.taxes import zero_money, zero_taxed_money
from ....discount.interface import fetch_variant_rules_info
from ....order import ORDER_EDITABLE_STATUS, OrderStatus, events
from ....order.error_codes import OrderErrorCode
from ....order.utils import invalidate_order_prices
from ....payment import PaymentError
from ....payment import models as payment_models
from ....plugins.manager import PluginsManager
from ....product import models as product_models
from ....shipping.interface import ShippingMethodData
from ....shipping.models import ShippingMethodChannelListing
from ..utils import get_shipping_method_availability_error

SHIPPING_METHOD_UPDATE_FIELDS = [
    "currency",
    "shipping_method",
    "shipping_price_net_amount",
    "shipping_price_gross_amount",
    "base_shipping_price_amount",
    "shipping_method_name",
    "shipping_tax_class",
    "shipping_tax_class_name",
    "shipping_tax_class_private_metadata",
    "shipping_tax_class_metadata",
    "shipping_tax_rate",
    "should_refresh_prices",
    "updated_at",
]


class EditableOrderValidationMixin:
    class Meta:
        abstract = True

    @classmethod
    def validate_order(cls, order):
        if order.status not in ORDER_EDITABLE_STATUS:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Only draft and unconfirmed orders can be edited.",
                        code=OrderErrorCode.NOT_EDITABLE.value,
                    )
                }
            )
        return order


class ShippingMethodUpdateMixin:
    class Meta:
        abstract = True

    @classmethod
    def clear_shipping_method_from_order(cls, order):
        order.shipping_method = None
        order.base_shipping_price = zero_money(order.currency)
        order.shipping_price = zero_taxed_money(order.currency)
        order.shipping_method_name = None
        order.shipping_tax_rate = None
        order.shipping_tax_class = None
        order.shipping_tax_class_name = None
        order.shipping_tax_class_private_metadata = {}
        order.shipping_tax_class_metadata = {}
        invalidate_order_prices(order)

    @classmethod
    def update_shipping_method(cls, order, method, shipping_method_data):
        order.shipping_method = method
        order.shipping_method_name = method.name

        tax_class = method.tax_class
        if tax_class:
            order.shipping_tax_class = tax_class
            order.shipping_tax_class_name = tax_class.name
            order.shipping_tax_class_private_metadata = tax_class.private_metadata
            order.shipping_tax_class_metadata = tax_class.metadata
        invalidate_order_prices(order)

    @classmethod
    def validate_shipping_channel_listing(cls, method, order):
        shipping_channel_listing = ShippingMethodChannelListing.objects.filter(
            shipping_method=method, channel=order.channel
        ).first()
        if not shipping_channel_listing:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method not available in the given channel.",
                        code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )
        return shipping_channel_listing

    @classmethod
    def _update_shipping_price(
        cls,
        order,
        shipping_channel_listing,
    ):
        if not shipping_channel_listing:
            order.base_shipping_price = zero_money(order.currency)
            return

        if (
            order.shipping_method
            and order.shipping_address
            and order.is_shipping_required()
        ):
            order.base_shipping_price = shipping_channel_listing.price
        else:
            order.base_shipping_price = zero_money(order.currency)


def clean_order_update_shipping(
    order, method: ShippingMethodData, manager: "PluginsManager"
):
    if not order.shipping_address:
        raise ValidationError(
            {
                "order": ValidationError(
                    "Cannot choose a shipping method for an order without "
                    "the shipping address.",
                    code=OrderErrorCode.ORDER_NO_SHIPPING_ADDRESS.value,
                )
            }
        )

    error = get_shipping_method_availability_error(order, method, manager)
    if error:
        raise ValidationError({"shipping_method": error})


def get_webhook_handler_by_order_status(status, manager):
    if status == OrderStatus.DRAFT:
        return manager.draft_order_updated
    else:
        return manager.order_updated


def try_payment_action(order, user, app, payment, func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        # provided order might alter it's total_paid.
        order.refresh_from_db()
        return result
    except (PaymentError, ValueError) as e:
        message = str(e)
        events.payment_failed_event(
            order=order, user=user, app=app, message=message, payment=payment
        )
        raise ValidationError(
            {
                "payment": ValidationError(
                    message, code=OrderErrorCode.PAYMENT_ERROR.value
                )
            }
        )


def clean_payment(payment: Optional[payment_models.Payment]) -> payment_models.Payment:
    if not payment:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "There's no payment associated with the order.",
                    code=OrderErrorCode.PAYMENT_MISSING.value,
                )
            }
        )
    return payment


VariantData = namedtuple("VariantData", ["variant", "rules_info"])


def get_variant_rule_info_map(
    variant_ids, channel_id, language_code=settings.LANGUAGE_CODE
):
    variant_id_to_variant_and_rules_info_map = {}
    variants = product_models.ProductVariant.objects.filter(
        pk__in=variant_ids
    ).prefetch_related(
        "channel_listings__variantlistingpromotionrule__promotion_rule__promotion",
        "channel_listings__variantlistingpromotionrule__promotion_rule__promotion__translations",
        "channel_listings__variantlistingpromotionrule__promotion_rule__translations",
    )
    for variant in variants:
        variant_channel_listing = get_variant_channel_listing(variant, channel_id)
        rules_info = fetch_variant_rules_info(variant_channel_listing, language_code)
        variant_id_to_variant_and_rules_info_map[
            graphene.Node.to_global_id("ProductVariant", variant.pk)
        ] = VariantData(variant=variant, rules_info=rules_info)

    return variant_id_to_variant_and_rules_info_map
