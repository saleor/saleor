import copy

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from prices import Money

from ....core.permissions import OrderPermissions
from ....order import OrderStatus, events, models
from ....order.error_codes import OrderErrorCode
from ....order.utils import (
    create_order_discount_for_order,
    get_order_discounts,
    recalculate_order,
    recalculate_order_discounts,
    recalculate_order_prices,
    remove_discount_from_order_line,
    remove_order_discount_from_order,
    update_discount_for_order_line,
)
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types.common import OrderError
from ...discount.enums import DiscountValueTypeEnum
from ...utils import get_user_or_app_from_context
from ..types import Order, OrderLine


class OrderDiscountCommonInput(graphene.InputObjectType):
    value_type = graphene.Field(
        DiscountValueTypeEnum,
        required=True,
        description="Type of the discount: fixed or percent",
    )
    value = PositiveDecimal(
        required=True,
        description="Value of the discount. Can store fixed value or percent value",
    )
    reason = graphene.String(
        required=False, description="Explanation for the applied discount."
    )


class OrderDiscountCommon(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def validate_order(cls, info, order):
        # This condition can be removed when we introduce discount for the rest type of
        # the orders.
        if order.status != OrderStatus.DRAFT:
            error_msg = "Only draft order can be modified."
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        error_msg, code=OrderErrorCode.CANNOT_DISCOUNT.value
                    )
                }
            )

    @classmethod
    def _validation_error_for_input_value(
        cls, error_msg, code=OrderErrorCode.INVALID.value
    ):
        return ValidationError({"value": ValidationError(error_msg, code=code)})

    @classmethod
    def validate_order_discount_input(cls, _info, max_total: Money, input: dict):
        value_type = input["value_type"]
        value = input["value"]
        if value_type == DiscountValueTypeEnum.FIXED:
            if value > max_total.amount:
                error_msg = (
                    f"The value ({value}) cannot be higher than {max_total.amount} "
                    f"{max_total.currency}"
                )
                raise cls._validation_error_for_input_value(error_msg)
        elif value > 100:
            error_msg = f"The percentage value ({value}) cannot be higher than 100."
            raise cls._validation_error_for_input_value(error_msg)

    @classmethod
    def recalculate_order(cls, order: models.Order):
        """Recalculate order data and save them."""
        recalculate_order_prices(order)
        recalculate_order_discounts(order)
        order.save(
            update_fields=[
                "total_net_amount",
                "total_gross_amount",
                "undiscounted_total_net_amount",
                "undiscounted_total_gross_amount",
            ]
        )


class OrderDiscountAdd(OrderDiscountCommon):
    order = graphene.Field(Order, description="Order which has been discounted.")

    class Arguments:
        order_id = graphene.ID(description="ID of an order to discount.", required=True)
        input = OrderDiscountCommonInput(
            required=True,
            description="Fields required to create a discount for the order.",
        )

    class Meta:
        description = "Adds discount to the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def validate_order(cls, info, order):
        super().validate_order(info, order)
        # This condition can be removed when we introduce support for multi discounts.
        order_discounts = get_order_discounts(order)
        if len(order_discounts) >= 1:
            error_msg = "Order already has assigned discount."
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        error_msg, code=OrderErrorCode.CANNOT_DISCOUNT.value
                    )
                }
            )

    @classmethod
    def validate(cls, info, order, input):
        cls.validate_order(info, order)
        cls.validate_order_discount_input(info, order.undiscounted_total.gross, input)

    @classmethod
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):
        requester = get_user_or_app_from_context(info.context)
        order = cls.get_node_or_error(info, data.get("order_id"), only_type=Order)
        input = data.get("input", {})
        cls.validate(info, order, input)

        reason = input.get("reason")
        value_type = input.get("value_type")
        value = input.get("value")

        order_discount = create_order_discount_for_order(
            order, reason, value_type, value
        )

        events.order_discount_added_event(
            order=order,
            user=requester,
            order_discount=order_discount,
        )
        return OrderDiscountAdd(order=order)


class OrderDiscountUpdate(OrderDiscountCommon):
    order = graphene.Field(Order, description="Order which has been discounted.")

    class Arguments:
        discount_id = graphene.ID(
            description="ID of a discount to update.", required=True
        )
        input = OrderDiscountCommonInput(
            required=True,
            description="Fields required to update a discount for the order.",
        )

    class Meta:
        description = "Update discount for the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def validate(cls, info, order, order_discount, input):
        cls.validate_order(info, order)
        input["value"] = input.get("value") or order_discount.value
        input["value_type"] = input.get("value_type") or order_discount.value_type

        cls.validate_order_discount_input(info, order.undiscounted_total.gross, input)

    @classmethod
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):
        requester = get_user_or_app_from_context(info.context)
        order_discount = cls.get_node_or_error(
            info, data.get("discount_id"), only_type="OrderDiscount"
        )
        order = order_discount.order
        input = data.get("input")
        cls.validate(info, order, order_discount, input)

        reason = input.get("reason", order_discount.reason)
        value_type = input.get("value_type", order_discount.value_type)
        value = input.get("value", order_discount.value)

        order_discount_before_update = copy.deepcopy(order_discount)

        order_discount.reason = reason
        order_discount.value = value
        order_discount.value_type = value_type
        order_discount.save()

        cls.recalculate_order(order)

        if (
            order_discount_before_update.value_type != value_type
            or order_discount_before_update.value != value
        ):
            # call update event only when we changed the type or value of the discount
            order_discount.refresh_from_db()
            events.order_discount_updated_event(
                order=order,
                user=requester,
                order_discount=order_discount,
                old_order_discount=order_discount_before_update,
            )
        return OrderDiscountUpdate(order=order)


class OrderDiscountDelete(OrderDiscountCommon):
    order = graphene.Field(Order, description="Order which has removed discount.")

    class Arguments:
        discount_id = graphene.ID(
            description="ID of a discount to remove.", required=True
        )

    class Meta:
        description = "Remove discount from the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):
        requester = get_user_or_app_from_context(info.context)
        order_discount = cls.get_node_or_error(
            info, data.get("discount_id"), only_type="OrderDiscount"
        )
        order = order_discount.order
        cls.validate_order(info, order)

        remove_order_discount_from_order(order, order_discount)
        events.order_discount_deleted_event(
            order=order,
            user=requester,
            order_discount=order_discount,
        )

        order.refresh_from_db()

        cls.recalculate_order(order)

        return OrderDiscountDelete(order=order)


class OrderLineDiscountUpdate(OrderDiscountCommon):
    order_line = graphene.Field(
        OrderLine, description="Order line which has been discounted."
    )
    order = graphene.Field(
        Order, description="Order which is related to the discounted line."
    )

    class Arguments:
        order_line_id = graphene.ID(
            description="ID of a order line to update price", required=True
        )
        input = OrderDiscountCommonInput(
            required=True,
            description="Fields required to update price for the order line.",
        )

    class Meta:
        description = "Update discount for the order line."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def validate(cls, info, order, order_line, input):
        cls.validate_order(info, order)
        input["value"] = input.get("value") or order_line.unit_discount_value
        input["value_type"] = input.get("value_type") or order_line.unit_discount_type

        cls.validate_order_discount_input(
            info, order_line.undiscounted_unit_price.gross, input
        )

    @classmethod
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):

        requester = get_user_or_app_from_context(info.context)
        order_line = cls.get_node_or_error(
            info, data.get("order_line_id"), only_type=OrderLine
        )
        input = data.get("input")
        order = order_line.order
        cls.validate(info, order, order_line, input)
        reason = input.get("reason")
        value_type = input.get("value_type")
        value = input.get("value")

        order_line_before_update = copy.deepcopy(order_line)
        tax_included = info.context.site.settings.include_taxes_in_prices

        update_discount_for_order_line(
            order_line,
            order=order,
            reason=reason,
            value_type=value_type,
            value=value,
            manager=info.context.plugins,
            tax_included=tax_included,
        )
        if (
            order_line_before_update.unit_discount_value != value
            or order_line_before_update.unit_discount_type != value_type
        ):
            # Create event only when we change type or value of the discount
            events.order_line_discount_updated_event(
                order=order,
                user=requester,
                line=order_line,
                line_before_update=order_line_before_update,
            )
            recalculate_order(order)
        return OrderLineDiscountUpdate(order_line=order_line, order=order)


class OrderLineDiscountRemove(OrderDiscountCommon):
    order_line = graphene.Field(
        OrderLine, description="Order line which has removed discount."
    )
    order = graphene.Field(
        Order, description="Order which is related to line which has removed discount."
    )

    class Arguments:
        order_line_id = graphene.ID(
            description="ID of a order line to remove its discount", required=True
        )

    class Meta:
        description = "Remove discount applied to the order line."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def validate(cls, info, order):
        cls.validate_order(info, order)

    @classmethod
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):
        tax_included = info.context.site.settings.include_taxes_in_prices
        requester = get_user_or_app_from_context(info.context)
        order_line = cls.get_node_or_error(
            info, data.get("order_line_id"), only_type=OrderLine
        )
        order = order_line.order
        cls.validate(info, order)

        remove_discount_from_order_line(
            order_line, order, manager=info.context.plugins, tax_included=tax_included
        )

        events.order_line_discount_removed_event(
            order=order,
            user=requester,
            line=order_line,
        )

        recalculate_order(order)
        return OrderLineDiscountRemove(order_line=order_line, order=order)
