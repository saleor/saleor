from collections import defaultdict
from typing import Dict, List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import OrderPermissions
from ....core.taxes import TaxError
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.error_codes import OrderErrorCode
from ....order.fetch import fetch_order_lines
from ....order.search import update_order_search_vector
from ....order.utils import (
    add_variant_to_order,
    invalidate_order_prices,
    recalculate_order_weight,
)
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, OrderError
from ...product.types import ProductVariant
from ..types import Order, OrderLine
from ..utils import (
    OrderLineData,
    validate_product_is_published_in_channel,
    validate_variant_channel_listings,
)
from .draft_order_create import OrderLineCreateInput
from .utils import EditableOrderValidationMixin, get_webhook_handler_by_order_status


class OrderLinesCreate(EditableOrderValidationMixin, BaseMutation):
    order = graphene.Field(Order, description="Related order.")
    order_lines = NonNullList(OrderLine, description="List of added order lines.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the order to add the lines to."
        )
        input = NonNullList(
            OrderLineCreateInput,
            required=True,
            description="Fields required to add order lines.",
        )

    class Meta:
        description = "Create order lines for an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
        errors_mapping = {"lines": "input", "channel": "input"}

    @classmethod
    def validate_lines(cls, info, data, existing_lines_info):
        grouped_lines_data: List[OrderLineData] = []
        lines_data_map: Dict[str, OrderLineData] = defaultdict(OrderLineData)

        variants_from_existing_lines = [
            line_info.line.variant_id for line_info in existing_lines_info
        ]

        invalid_ids = []
        for input_line in data.get("input"):
            variant_id = input_line["variant_id"]
            force_new_line = input_line["force_new_line"]
            variant = cls.get_node_or_error(
                info, variant_id, "variant_id", only_type=ProductVariant
            )
            quantity = input_line["quantity"]

            if quantity > 0:
                if force_new_line or variants_from_existing_lines.count(variant.pk) > 1:
                    grouped_lines_data.append(
                        OrderLineData(
                            variant_id=str(variant.id),
                            variant=variant,
                            quantity=quantity,
                        )
                    )
                else:
                    line_id = cls._find_line_id_for_variant_if_exist(
                        variant.pk, existing_lines_info
                    )

                    if line_id:
                        line_data = lines_data_map[line_id]
                        line_data.line_id = line_id
                    else:
                        line_data = lines_data_map[str(variant.id)]
                        line_data.variant_id = str(variant.id)

                    line_data.variant = variant
                    line_data.quantity += quantity
            else:
                invalid_ids.append(variant_id)
        if invalid_ids:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "Variants quantity must be greater than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY,
                        params={"variants": invalid_ids},
                    ),
                }
            )

        grouped_lines_data += list(lines_data_map.values())
        return grouped_lines_data

    @classmethod
    def validate_variants(cls, order, variants):
        try:
            channel = order.channel
            validate_product_is_published_in_channel(variants, channel)
            validate_variant_channel_listings(variants, channel)
        except ValidationError as error:
            cls.remap_error_fields(error, cls._meta.errors_mapping)
            raise ValidationError(error)

    @staticmethod
    def add_lines_to_order(order, lines_data, user, app, manager, settings, discounts):
        added_lines: List[OrderLine] = []
        try:
            for line_data in lines_data:
                line = add_variant_to_order(
                    order,
                    line_data,
                    user,
                    app,
                    manager,
                    settings,
                    discounts=discounts,
                    allocate_stock=order.is_unconfirmed(),
                )
                added_lines.append(line)
        except TaxError as tax_error:
            raise ValidationError(
                "Unable to calculate taxes - %s" % str(tax_error),
                code=OrderErrorCode.TAX_ERROR.value,
            )
        return added_lines

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        cls.validate_order(order)
        existing_lines_info = fetch_order_lines(order)

        lines_to_add = cls.validate_lines(info, data, existing_lines_info)
        variants = [line.variant for line in lines_to_add]
        cls.validate_variants(order, variants)

        added_lines = cls.add_lines_to_order(
            order,
            lines_to_add,
            info.context.user,
            info.context.app,
            info.context.plugins,
            info.context.site.settings,
            info.context.discounts,
        )

        # Create the products added event
        events.order_added_products_event(
            order=order,
            user=info.context.user,
            app=info.context.app,
            order_lines=added_lines,
        )

        invalidate_order_prices(order)
        recalculate_order_weight(order)
        update_order_search_vector(order, save=False)
        order.save(
            update_fields=[
                "should_refresh_prices",
                "weight",
                "search_vector",
                "updated_at",
            ]
        )
        func = get_webhook_handler_by_order_status(order.status, info)
        transaction.on_commit(lambda: func(order))

        return OrderLinesCreate(order=order, order_lines=added_lines)

    @classmethod
    def _find_line_id_for_variant_if_exist(cls, variant_id, lines_info):
        """Return line id by using provided variantId parameter."""
        if not lines_info:
            return

        line_info = list(
            filter(lambda x: (x.variant.pk == int(variant_id)), lines_info)
        )

        if not line_info or len(line_info) > 1:
            return

        return str(line_info[0].line.id)
