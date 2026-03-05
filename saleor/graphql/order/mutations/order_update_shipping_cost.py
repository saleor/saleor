from decimal import Decimal
from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....core.prices import quantize_price
from ....order import models
from ....order.actions import call_order_event
from ....order.error_codes import OrderErrorCode
from ....order.utils import get_order_country
from ....permission.enums import OrderPermissions
from ....tax.models import TaxClassCountryRate
from ....tax.utils import (
    get_tax_country_for_order,
    get_zero_rated_export_tax_class,
    normalize_tax_rate_for_db,
    resolve_tax_class_country_rate,
)
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types import BaseInputObjectType, OrderError
from ...core.validators import validate_price_precision
from ...plugins.dataloaders import get_plugin_manager_promise
from ...tax.types import TaxClass as TaxClassType
from ..types import Order
from .utils import EditableOrderValidationMixin


class OrderUpdateShippingCostInput(BaseInputObjectType):
    shipping_cost_net = PositiveDecimal(
        description="Net shipping cost amount (excluding VAT).",
        required=True,
    )
    tax_class = graphene.ID(
        description=(
            "Tax class used to determine the VAT rate for shipping. "
            "The rate is looked up from the tax class's country rate for the "
            "order's shipping address country. "
            "If omitted, the order's existing shipping tax class is reused; "
            "if none is set, the country default rate applies. "
            "Ignored for non-DDP exports, which always use the site-wide "
            "zero_rated_export_tax_class."
        ),
        required=False,
    )
    inco_term = graphene.String(
        description=(
            "Incoterm (International Commercial Terms) defining shipping "
            "responsibility. Options: EXW, FCA, CPT, CIP, DAP, DPU, DDP, "
            "FAS, FOB, CFR, CIF."
        ),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderUpdateShippingCost(EditableOrderValidationMixin, BaseMutation):
    order = graphene.Field(Order, description="Order with updated shipping cost.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of the order to update shipping cost.",
        )
        input = OrderUpdateShippingCostInput(
            description="Fields required to update shipping cost.",
            required=True,
        )

    class Meta:
        description = (
            "Manually sets the shipping cost of a draft or unconfirmed order. "
            "Provide the net amount and optionally a tax class; the gross is "
            "derived from the tax class's rate for the order's shipping country."
        )
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def _get_or_create_manual_shipping_method(cls, channel):
        from ....shipping.models import (
            ShippingMethod,
            ShippingMethodChannelListing,
            ShippingZone,
        )

        manual_zone, _ = ShippingZone.objects.get_or_create(
            name="MANUAL",
            defaults={
                "countries": [],
                "description": "Automatic zone for manual shipping costs",
            },
        )

        if not manual_zone.channels.filter(id=channel.id).exists():
            manual_zone.channels.add(channel)

        manual_method, created = ShippingMethod.objects.get_or_create(
            shipping_zone=manual_zone,
            name="MANUAL",
            defaults={"type": "manual"},
        )

        if not created and manual_method.type != "manual":
            manual_method.type = "manual"
            manual_method.save(update_fields=["type"])

        ShippingMethodChannelListing.objects.get_or_create(
            shipping_method=manual_method,
            channel=channel,
            defaults={
                "minimum_order_price_amount": Decimal(0),
                "price_amount": Decimal(0),
                "currency": channel.currency_code,
            },
        )

        return manual_method

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        order = cls.get_node_or_error(
            info,
            data["id"],
            only_type=Order,
            qs=models.Order.objects.select_related("channel").prefetch_related("lines"),
        )
        order = cast(models.Order, order)
        input = data["input"]

        cls.check_channel_permissions(info, [order.channel_id])
        cls.validate_order(order)

        if not order.is_shipping_required():
            raise ValidationError(
                {
                    "order": ValidationError(
                        "Cannot set shipping cost for order without shippable products.",
                        code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )

        from ....shipping import IncoTerm

        inco_term = input.get("inco_term")
        if inco_term and inco_term not in [choice[0] for choice in IncoTerm.CHOICES]:
            raise ValidationError(
                {
                    "inco_term": ValidationError(
                        f"Invalid inco_term. Must be one of: "
                        f"{', '.join([c[0] for c in IncoTerm.CHOICES])}",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )

        if inco_term == IncoTerm.DDP:
            country = get_order_country(order)
            line_tax_class_ids = {
                line.tax_class_id
                for line in order.lines.all()
                if line.tax_class_id is not None
            }
            if line_tax_class_ids:
                existing = set(
                    TaxClassCountryRate.objects.filter(
                        tax_class_id__in=line_tax_class_ids,
                        country=country,
                    ).values_list("tax_class_id", flat=True)
                )
                missing = line_tax_class_ids - existing
                if missing:
                    raise ValidationError(
                        {
                            "inco_term": ValidationError(
                                f"Cannot set inco_term to DDP: no tax rate configured for "
                                f"country '{country}' on {len(missing)} tax class(es).",
                                code=OrderErrorCode.TAX_ERROR.value,
                            )
                        }
                    )

        # Resolve explicit tax class from input (may be overridden below for exports).
        tax_class_id = input.get("tax_class")
        if tax_class_id:
            tax_class = cls.get_node_or_error(
                info, tax_class_id, only_type=TaxClassType, field="tax_class"
            )
        else:
            tax_class = order.shipping_tax_class

        # Apply inco_term so get_zero_rated_export_tax_class sees the new value.
        if inco_term:
            order.inco_term = inco_term

        # Non-DDP exports always use zero_rated_export_tax_class — consistent with
        # update_order_prices_with_flat_rates. Explicit tax_class input is ignored.
        try:
            export_tax_class = get_zero_rated_export_tax_class(order)
        except ValueError as e:
            raise ValidationError(
                {
                    "inco_term": ValidationError(
                        str(e), code=OrderErrorCode.INVALID.value
                    )
                }
            ) from e
        if export_tax_class is not None:
            tax_class = export_tax_class

        country_code = get_tax_country_for_order(order)
        if country_code is None:
            shipping_country_rate = None
        else:
            shipping_country_rate = resolve_tax_class_country_rate(order, tax_class)
        tax_rate = shipping_country_rate.rate if shipping_country_rate else Decimal(0)

        net_amount = input["shipping_cost_net"]
        currency = order.currency
        try:
            validate_price_precision(net_amount, currency)
        except ValidationError as error:
            error.code = OrderErrorCode.INVALID.value
            raise ValidationError({"shipping_cost_net": error}) from error
        gross_amount = quantize_price(
            net_amount * (Decimal(1) + tax_rate / Decimal(100)), currency
        )

        old_shipping_net = order.shipping_price_net_amount
        old_shipping_gross = order.shipping_price_gross_amount

        order.shipping_price_net_amount = net_amount
        order.shipping_price_gross_amount = gross_amount
        order.base_shipping_price_amount = net_amount
        order.undiscounted_base_shipping_price_amount = net_amount
        order.shipping_tax_rate = normalize_tax_rate_for_db(tax_rate)
        order.shipping_xero_tax_code = (
            shipping_country_rate.xero_tax_code if shipping_country_rate else None
        )

        order.total_net_amount = quantize_price(
            order.total_net_amount - old_shipping_net + net_amount, currency
        )
        order.total_gross_amount = quantize_price(
            order.total_gross_amount - old_shipping_gross + gross_amount, currency
        )
        order.undiscounted_total_net_amount = quantize_price(
            order.undiscounted_total_net_amount - old_shipping_net + net_amount,
            currency,
        )
        order.undiscounted_total_gross_amount = quantize_price(
            order.undiscounted_total_gross_amount - old_shipping_gross + gross_amount,
            currency,
        )

        needs_manual_method = not order.shipping_method
        if needs_manual_method:
            order.shipping_method_name = "Manual Shipping Cost"
            manual_method = cls._get_or_create_manual_shipping_method(order.channel)
            order.shipping_method = manual_method

        # When inco_term changes, line taxes may need recalculating on the next
        # access (e.g. switching from DDP to EXW changes line tax classes).
        # Save should_refresh_prices=True to DB but keep it False in memory so
        # the current response reflects the inline calculation, not a re-fetch.
        order.should_refresh_prices = bool(inco_term)

        update_fields = [
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "base_shipping_price_amount",
            "undiscounted_base_shipping_price_amount",
            "shipping_tax_rate",
            "shipping_xero_tax_code",
            "total_net_amount",
            "total_gross_amount",
            "undiscounted_total_net_amount",
            "undiscounted_total_gross_amount",
            "should_refresh_prices",
            "updated_at",
        ]
        effective_tax_class = export_tax_class or (tax_class if tax_class_id else None)
        if effective_tax_class:
            order.shipping_tax_class = effective_tax_class
            order.shipping_tax_class_name = effective_tax_class.name
            order.shipping_tax_class_metadata = effective_tax_class.metadata
            order.shipping_tax_class_private_metadata = (
                effective_tax_class.private_metadata
            )
            update_fields.extend(
                [
                    "shipping_tax_class",
                    "shipping_tax_class_name",
                    "shipping_tax_class_metadata",
                    "shipping_tax_class_private_metadata",
                ]
            )
        if needs_manual_method:
            update_fields.extend(["shipping_method", "shipping_method_name"])
        if inco_term:
            update_fields.append("inco_term")

        order.save(update_fields=update_fields)
        # Reset in memory so resolve_shipping_price uses the inline values above,
        # not a TAX_APP recalculation that would ignore our flat-rate calculation.
        order.should_refresh_prices = False

        manager = get_plugin_manager_promise(info.context).get()
        event_to_emit = (
            WebhookEventAsyncType.DRAFT_ORDER_UPDATED
            if order.is_draft()
            else WebhookEventAsyncType.ORDER_UPDATED
        )
        call_order_event(manager, event_to_emit, order)

        return OrderUpdateShippingCost(order=SyncWebhookControlContext(order))
