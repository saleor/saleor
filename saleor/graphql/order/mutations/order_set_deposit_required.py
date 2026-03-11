from decimal import Decimal as DecimalType

import graphene
from django.core.exceptions import ValidationError

from ....order.error_codes import OrderErrorCode
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.scalars import Decimal
from ...core.types import OrderError
from ..types import Order


class OrderSetDepositRequired(BaseMutation):
    order = graphene.Field(Order, description="Order with updated deposit settings.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order.")
        required = graphene.Boolean(
            required=True, description="Whether deposit is required."
        )
        percentage = Decimal(
            required=False,
            description="Percentage of total required as deposit (0-100).",
        )
        xero_bank_account_code = graphene.String(
            required=False,
            description="Xero bank account code to use for deposit prepayments.",
        )
        xero_bank_account_sort_code = graphene.String(
            required=False,
            description="Bank sort code for the selected Xero bank account.",
        )
        xero_bank_account_number = graphene.String(
            required=False,
            description="Bank account number for the selected Xero bank account.",
        )

    class Meta:
        description = "Set whether an order requires a deposit before fulfillment."
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_input(cls, required, percentage, xero_bank_account_code):
        if required:
            if percentage is not None and not (
                DecimalType(0) <= percentage <= DecimalType(100)
            ):
                raise ValidationError(
                    {
                        "percentage": ValidationError(
                            "Deposit percentage must be between 0 and 100.",
                            code=OrderErrorCode.INVALID.value,
                        )
                    }
                )
            if not xero_bank_account_code:
                raise ValidationError(
                    {
                        "xero_bank_account_code": ValidationError(
                            "A Xero bank account must be selected when enabling deposit.",
                            code=OrderErrorCode.INVALID.value,
                        )
                    }
                )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id,
        required,
        percentage=None,
        xero_bank_account_code=None,
        xero_bank_account_sort_code=None,
        xero_bank_account_number=None,
    ):
        order = cls.get_node_or_error(info, id, only_type=Order)
        cls.check_channel_permissions(info, [order.channel_id])

        if order.payments.xero_unpaid_deposits().exists():
            raise ValidationError(
                "Deposit settings cannot be changed while unpaid deposit prepayments exist. "
                "Delete the unpaid prepayments first.",
                code=OrderErrorCode.INVALID.value,
            )

        cls.clean_input(required, percentage, xero_bank_account_code)

        order.deposit_required = required
        order.deposit_percentage = percentage if required else None
        update_fields = ["deposit_required", "deposit_percentage"]
        if not required:
            order.xero_bank_account_code = None
            order.xero_bank_account_sort_code = None
            order.xero_bank_account_number = None
            update_fields += [
                "xero_bank_account_code",
                "xero_bank_account_sort_code",
                "xero_bank_account_number",
            ]
        else:
            if xero_bank_account_code is not None:
                order.xero_bank_account_code = xero_bank_account_code
                update_fields.append("xero_bank_account_code")
            if xero_bank_account_sort_code is not None:
                order.xero_bank_account_sort_code = xero_bank_account_sort_code
                update_fields.append("xero_bank_account_sort_code")
            if xero_bank_account_number is not None:
                order.xero_bank_account_number = xero_bank_account_number
                update_fields.append("xero_bank_account_number")
        order.save(update_fields=update_fields)

        return OrderSetDepositRequired(order=SyncWebhookControlContext(order))
