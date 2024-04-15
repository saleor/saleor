from typing import Any, Union, cast

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from graphql import GraphQLError

from ....order import OrderGrantedRefundStatus, models
from ....order.utils import update_order_charge_data
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.descriptions import (
    ADDED_IN_313,
    ADDED_IN_315,
    ADDED_IN_320,
    PREVIEW_FEATURE,
)
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.scalars import Decimal
from ...core.types import BaseInputObjectType
from ...core.types.common import Error, NonNullList
from ...core.utils import from_global_id_or_error
from ...payment.types import TransactionItem
from ..enums import OrderGrantRefundUpdateErrorCode, OrderGrantRefundUpdateLineErrorCode
from ..types import Order, OrderGrantedRefund
from .order_grant_refund_utils import (
    assign_order_lines,
    get_input_lines_data,
    handle_lines_with_quantity_already_refunded,
    shipping_costs_already_granted,
)


class OrderGrantRefundUpdateLineError(Error):
    code = OrderGrantRefundUpdateLineErrorCode(
        description="The error code.", required=True
    )
    line_id = graphene.ID(
        description="The ID of the line related to the error.", required=True
    )


class OrderGrantRefundUpdateError(Error):
    code = OrderGrantRefundUpdateErrorCode(description="The error code.", required=True)

    add_lines = NonNullList(
        OrderGrantRefundUpdateLineError,
        description="List of lines to add which cause the error."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
        required=False,
    )
    remove_lines = NonNullList(
        OrderGrantRefundUpdateLineError,
        description="List of lines to remove which cause the error."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderGrantRefundUpdateLineAddInput(BaseInputObjectType):
    id = graphene.ID(description="The ID of the order line.", required=True)
    quantity = graphene.Int(
        description="The quantity of line items to be marked to refund.", required=True
    )
    reason = graphene.String(description="Reason of the granted refund for the line.")

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderGrantRefundUpdateInput(BaseInputObjectType):
    amount = Decimal(
        description=(
            "Amount of the granted refund. if not provided and `addLines` or "
            "`removeLines` or `grantRefundForShipping` is provided, amount will be "
            "calculated automatically."
        )
    )
    reason = graphene.String(description="Reason of the granted refund.")
    add_lines = NonNullList(
        OrderGrantRefundUpdateLineAddInput,
        description="Lines to assign to granted refund."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
        required=False,
    )
    remove_lines = NonNullList(
        graphene.ID,
        description="Lines to remove from granted refund."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
        required=False,
    )
    grant_refund_for_shipping = graphene.Boolean(
        description="Determine if granted refund should include shipping costs."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
        required=False,
    )
    transaction_id = graphene.ID(
        description=(
            "The ID of the transaction item related to the granted refund. "
            "If `amount` provided in the input, the transaction.chargedAmount needs to "
            "be equal or greater than provided `amount`."
            "If `amount` is not provided in the input and calculated automatically by "
            "Saleor, the `min(calculatedAmount, transaction.chargedAmount)` will be "
            "used."
            "Field will be required starting from Saleor 3.21."
            + ADDED_IN_320
            + PREVIEW_FEATURE
        ),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderGrantRefundUpdate(BaseMutation):
    order = graphene.Field(
        Order, description="Order which has assigned updated grant refund."
    )
    granted_refund = graphene.Field(
        OrderGrantedRefund, description="Created granted refund."
    )

    class Arguments:
        id = graphene.ID(description="ID of the granted refund.", required=True)
        input = OrderGrantRefundUpdateInput(
            required=True,
            description="Fields required to update a granted refund.",
        )

    class Meta:
        description = "Updates granted refund." + ADDED_IN_313 + PREVIEW_FEATURE
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderGrantRefundUpdateError
        doc_category = DOC_CATEGORY_ORDERS

    @classmethod
    def validate_input(
        cls, input: dict[str, Any], granted_refund: models.OrderGrantedRefund
    ):
        amount = input.get("amount")
        reason = input.get("reason")
        input_lines = input.get("add_lines", [])
        remove_lines = input.get("remove_lines", [])
        grant_refund_for_shipping = input.get("grant_refund_for_shipping", False)
        transaction_id = input.get("transaction_id")
        if (
            amount is None
            and reason is None
            and not input_lines
            and not grant_refund_for_shipping
            and not remove_lines
            and not transaction_id
        ):
            error_msg = "At least one field needs to be provided to process update."
            raise ValidationError(
                {
                    "input": ValidationError(
                        error_msg, code=OrderGrantRefundUpdateErrorCode.REQUIRED.value
                    )
                }
            )
        only_reason_provided = reason is not None and len(input) == 1
        if (
            granted_refund.status
            in [OrderGrantedRefundStatus.PENDING, OrderGrantedRefundStatus.SUCCESS]
            and not only_reason_provided
        ):
            fields_from_input = set(input.keys())
            if "reason" in fields_from_input:
                fields_from_input.remove("reason")
            error_msg = (
                "Only reason can be updated when `OrderGrantedRefund.status` is PENDING"
                " or SUCCESS."
            )
            raise ValidationError(
                {
                    error_field: ValidationError(
                        error_msg, code=OrderGrantRefundUpdateErrorCode.INVALID.value
                    )
                    for error_field in fields_from_input
                }
            )

    @classmethod
    def clean_remove_lines(
        cls,
        granted_refund: models.OrderGrantedRefund,
        lines_to_remove: list[str],
        errors: list[dict[str, Any]],
    ):
        lines_pk_to_remove = set()
        for line_id in lines_to_remove:
            try:
                _, pk = from_global_id_or_error(
                    line_id, only_type="OrderGrantedRefundLine", raise_error=True
                )
                lines_pk_to_remove.add(int(pk))
            except GraphQLError as e:
                errors.append(
                    {
                        "line_id": line_id,
                        "code": OrderGrantRefundUpdateLineErrorCode.GRAPHQL_ERROR.value,
                        "message": str(e),
                    }
                )
        line_ids_from_granted_refund = granted_refund.lines.filter(
            id__in=lines_pk_to_remove
        ).values_list("id", flat=True)
        invalid_ids = lines_pk_to_remove.difference(set(line_ids_from_granted_refund))
        if invalid_ids:
            for invalid_id in invalid_ids:
                errors.append(
                    {
                        "line_id": graphene.Node.to_global_id(
                            "OrderGrantedRefundLine", invalid_id
                        ),
                        "message": "Could not resolve to a line.",
                        "code": OrderGrantRefundUpdateLineErrorCode.NOT_FOUND.value,
                    }
                )

        return lines_pk_to_remove

    @classmethod
    def clean_add_lines(
        cls,
        order: models.Order,
        lines: list[dict[str, Union[str, int]]],
        errors: list[dict[str, Any]],
        line_ids_exclude: list[int],
    ) -> list[models.OrderGrantedRefundLine]:
        input_lines_data = get_input_lines_data(
            lines, errors, OrderGrantRefundUpdateLineErrorCode.GRAPHQL_ERROR.value
        )
        assign_order_lines(
            order,
            input_lines_data,
            errors,
            OrderGrantRefundUpdateLineErrorCode.NOT_FOUND.value,
        )
        handle_lines_with_quantity_already_refunded(
            order,
            input_lines_data,
            errors,
            OrderGrantRefundUpdateLineErrorCode.QUANTITY_GREATER_THAN_AVAILABLE.value,
            granted_refund_lines_to_exclude=line_ids_exclude,
        )

        return list(input_lines_data.values())

    @classmethod
    def clean_input(
        cls,
        info: ResolveInfo,
        granted_refund: models.OrderGrantedRefund,
        input: dict[str, Any],
    ):
        add_errors: list[dict[str, Any]] = []
        remove_errors: list[dict[str, Any]] = []
        errors = {}
        cls.validate_input(input, granted_refund)
        order = granted_refund.order
        amount = input.get("amount")
        reason = input.get("reason", None)
        transaction_id = input.get("transaction_id")
        add_lines = input.get("add_lines", [])
        remove_lines = input.get("remove_lines", [])
        grant_refund_for_shipping = input.get("grant_refund_for_shipping", None)

        line_ids_to_remove = []
        if remove_lines:
            line_ids_to_remove = cls.clean_remove_lines(
                granted_refund, remove_lines, remove_errors
            )

        if remove_errors:
            errors["remove_lines"] = ValidationError(
                "Provided input for lines is invalid.",
                code=OrderGrantRefundUpdateErrorCode.INVALID.value,
                params={"remove_lines": remove_errors},
            )

        lines_to_add = []
        if add_lines:
            lines_to_add = cls.clean_add_lines(
                order, add_lines, add_errors, line_ids_to_remove
            )
            for line in lines_to_add:
                line.granted_refund = granted_refund

        if add_errors:
            errors["add_lines"] = ValidationError(
                "Provided input for lines is invalid.",
                code=OrderGrantRefundUpdateErrorCode.INVALID.value,
                params={"add_lines": add_errors},
            )

        if grant_refund_for_shipping and shipping_costs_already_granted(
            order, grant_refund_pk_to_exclude=granted_refund.pk
        ):
            error_code = OrderGrantRefundUpdateErrorCode.SHIPPING_COSTS_ALREADY_GRANTED
            errors["grant_refund_for_shipping"] = ValidationError(
                "Shipping costs have already been granted.",
                code=error_code.value,
            )

        transaction_item = granted_refund.transaction_item
        if transaction_id is not None:
            transaction_item = cls.get_node_or_error(
                info, transaction_id, only_type=TransactionItem
            )

        amount_not_changed = (
            not add_lines
            and not remove_lines
            and amount is None
            and not grant_refund_for_shipping
        )

        # if transaction item is assigned, we need to validate if the provider amount is
        # not greater than the current charged amount of the transaction.
        if transaction_item and amount is not None:
            if amount > transaction_item.charged_value:
                code = (
                    OrderGrantRefundUpdateErrorCode.AMOUNT_GREATER_THAN_AVAILABLE.value
                )
                errors["amount"] = ValidationError(
                    "Amount cannot be greater than the charged amount of provided "
                    "transaction.",
                    code=code,
                )
        # if transaction id is provided in the input, we need to validate if the
        # provided transaction have enough charged amount to cover the granted
        # refund.
        elif transaction_id and transaction_item and amount_not_changed:
            amount = granted_refund.amount_value
            charged_value = cast(Decimal, transaction_item.charged_value)
            if amount > charged_value:
                code = (
                    OrderGrantRefundUpdateErrorCode.AMOUNT_GREATER_THAN_AVAILABLE.value
                )
                errors["transaction_id"] = ValidationError(
                    "Provided transaction does not have enough charged amount to cover"
                    " the granted refund.",
                    code=code,
                )

        if errors:
            raise ValidationError(errors)

        cleaned_input = {
            "amount": amount,
            "reason": reason,
            "add_lines": lines_to_add,
            "remove_lines": line_ids_to_remove,
            "grant_refund_for_shipping": grant_refund_for_shipping,
            "transaction_item": transaction_item,
        }
        return cleaned_input

    @classmethod
    def process_update_for_granted_refund(
        cls,
        order: models.Order,
        granted_refund: models.OrderGrantedRefund,
        cleaned_input: dict,
    ):
        lines_to_remove = cleaned_input.get("remove_lines")
        lines_to_add = cleaned_input.get("add_lines")
        grant_refund_for_shipping = cleaned_input.get("grant_refund_for_shipping")
        if grant_refund_for_shipping is not None:
            granted_refund.shipping_costs_included = grant_refund_for_shipping

        transaction_item = cleaned_input.get("transaction_item")
        if transaction_item:
            granted_refund.transaction_item = transaction_item
        with transaction.atomic():
            if lines_to_remove:
                granted_refund.lines.filter(id__in=lines_to_remove).delete()
            if lines_to_add:
                granted_refund.lines.bulk_create(lines_to_add)

            amount = cleaned_input.get("amount")
            if amount is not None:
                granted_refund.amount_value = amount
            elif amount is None and (
                lines_to_add or lines_to_remove or grant_refund_for_shipping is not None
            ):
                lines = granted_refund.lines.select_related("order_line")
                amount = sum(
                    [
                        line.order_line.unit_price_gross_amount * line.quantity
                        for line in lines
                    ]
                )
                if granted_refund.shipping_costs_included:
                    amount += order.shipping_price_gross_amount
                if transaction_item:
                    amount = min(amount, transaction_item.charged_value)
                granted_refund.amount_value = amount

            reason = cleaned_input.get("reason")
            if reason is not None:
                granted_refund.reason = reason

            granted_refund.save(
                update_fields=[
                    "amount_value",
                    "reason",
                    "shipping_costs_included",
                    "updated_at",
                    "transaction_item",
                ]
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        granted_refund = cls.get_node_or_error(
            info,
            id,
            only_type=OrderGrantedRefund,
            qs=models.OrderGrantedRefund.objects.select_related("transaction_item"),
        )
        order = granted_refund.order

        cleaned_input = cls.clean_input(info, granted_refund, input)
        cls.process_update_for_granted_refund(order, granted_refund, cleaned_input)
        update_order_charge_data(order)
        return cls(order=order, granted_refund=granted_refund)
