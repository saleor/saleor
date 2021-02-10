import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import OrderPermissions
from ....order import OrderStatus
from ....order.error_codes import OrderErrorCode
from ....order.utils import (
    create_order_discount_for_order,
    get_order_discounts,
    recalculate_order,
    remove_discount_from_order_line,
    remove_order_discount_from_order,
    update_discount_for_order_line,
    update_order_discount_for_order,
)
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types.common import OrderError
from ...discount.enums import DiscountValueTypeEnum
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

    # FIXME add value validation when value type is percentage - value <= 100
    # FIXME add value validation when value type is fixed order.total <= value


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
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):
        order = cls.get_node_or_error(info, data.get("order_id"), only_type=Order)
        cls.validate_order(info, order)
        input = data.get("input", {})

        reason = input.get("reason")
        value_type = input.get("value_type")
        value = input.get("value")
        create_order_discount_for_order(order, reason, value_type, value)
        # FIXME call tax plugins here
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
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):
        order_discount = cls.get_node_or_error(
            info, data.get("discount_id"), only_type="OrderDiscount"
        )
        order = order_discount.order
        cls.validate_order(info, order)
        input = data.get("input")

        reason = input.get("reason")
        value_type = input.get("value_type")
        value = input.get("value")

        update_order_discount_for_order(
            order, order_discount, reason=reason, value_type=value_type, value=value
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
        order_discount = cls.get_node_or_error(
            info, data.get("discount_id"), only_type="OrderDiscount"
        )
        order = order_discount.order
        remove_order_discount_from_order(order, order_discount)
        order.refresh_from_db()
        return OrderDiscountDelete(order=order)
        # FIXME call order event here. Update webhook payload


class OrderLineDiscountUpdate(BaseMutation):
    order_line = graphene.Field(
        OrderLine, description="Order line which has been discounted."
    )

    class Arguments:
        order_line_id = graphene.ID(
            description="ID of a order_line to update price", required=True
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

    # FIXME add value validation when value type is percentage - value <= 100
    # FIXME add value validation when value type is fixed order.total <= value
    @classmethod
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):
        order_line = cls.get_node_or_error(
            info, data.get("order_line_id"), only_type=OrderLine
        )
        input = data.get("input")
        reason = input.get("reason")
        value_type = input.get("value_type")
        value = input.get("value")

        order = order_line.order
        update_discount_for_order_line(
            order_line,
            order=order,
            reason=reason,
            value_type=value_type,
            value=value,
            manager=info.context.plugins,
        )
        recalculate_order(order)
        return OrderLineDiscountUpdate(order_line=order_line)


# FIXME is it proper name?
class OrderLineDiscountRemove(BaseMutation):
    order_line = graphene.Field(
        OrderLine, description="Order line which has removed discount."
    )

    class Arguments:
        order_line_id = graphene.ID(
            description="ID of a order_line to remove its discount", required=True
        )

    class Meta:
        description = "Remove discount applied to the order line."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    @transaction.atomic
    def perform_mutation(cls, root, info, **data):
        order_line = cls.get_node_or_error(
            info, data.get("order_line_id"), only_type=OrderLine
        )
        order = order_line.order
        remove_discount_from_order_line(order_line, order, manager=info.context.plugins)
        recalculate_order(order)
        return OrderLineDiscountRemove(order_line=order_line)
