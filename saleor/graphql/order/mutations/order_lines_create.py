from typing import List, Tuple

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import OrderPermissions
from ....core.taxes import TaxError
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.error_codes import OrderErrorCode
from ....order.search import update_order_search_document
from ....order.utils import add_variant_to_order, recalculate_order
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, OrderError
from ...product.types import ProductVariant
from ..types import Order, OrderLine
from ..utils import (
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
    def validate_lines(cls, info, data):
        lines_to_add = []
        invalid_ids = []
        for input_line in data.get("input"):
            variant_id = input_line["variant_id"]
            variant = cls.get_node_or_error(
                info, variant_id, "variant_id", only_type=ProductVariant
            )
            quantity = input_line["quantity"]
            if quantity > 0:
                lines_to_add.append((quantity, variant))
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
        return lines_to_add

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
    def add_lines_to_order(
        order, lines_to_add, user, app, manager, settings, discounts
    ):
        added_lines: List[Tuple[int, OrderLine]] = []
        try:
            for quantity, variant in lines_to_add:
                line = add_variant_to_order(
                    order,
                    variant,
                    quantity,
                    user,
                    app,
                    manager,
                    settings,
                    discounts=discounts,
                    allocate_stock=order.is_unconfirmed(),
                )
                added_lines.append((quantity, line))
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
        lines_to_add = cls.validate_lines(info, data)
        variants = [line[1] for line in lines_to_add]
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

        lines = [line for _, line in added_lines]

        recalculate_order(order)
        update_order_search_document(order)

        func = get_webhook_handler_by_order_status(order.status, info)
        transaction.on_commit(lambda: func(order))

        return OrderLinesCreate(order=order, order_lines=lines)
