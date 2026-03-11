from decimal import Decimal

import graphene
from django.core.exceptions import ValidationError

from ....order.error_codes import OrderErrorCode
from ....order.utils import update_order_charge_data
from ....payment import ChargeStatus, CustomPaymentChoices
from ....payment.models import Payment
from ....payment.utils_xero import get_reconciled_amount
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order


class OrderCheckPrepayment(BaseMutation):
    order = graphene.Field(Order, description="Order the prepayment belongs to.")

    class Arguments:
        order_id = graphene.ID(required=True, description="ID of the order.")
        psp_reference = graphene.String(
            required=True,
            description="Xero bank transaction ID of the prepayment to check.",
        )

    class Meta:
        description = (
            "Check the status of a Xero prepayment and update the local Payment "
            "record. If the prepayment has been reconciled in Xero, marks the "
            "payment as paid. If the prepayment no longer exists in Xero, deletes "
            "the local Payment record."
        )
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        order_id,
        psp_reference,
    ):
        order = cls.get_node_or_error(info, order_id, only_type=Order)
        cls.check_channel_permissions(info, [order.channel_id])

        try:
            payment = Payment.objects.get(
                order=order,
                gateway=CustomPaymentChoices.XERO,
                psp_reference=psp_reference,
                is_active=True,
            )
        except Payment.DoesNotExist:
            raise ValidationError(
                "No active prepayment found with this psp_reference on this order.",
                code=OrderErrorCode.INVALID.value,
            ) from None

        manager = get_plugin_manager_promise(info.context).get()
        response = manager.xero_check_prepayment_status(psp_reference)

        if response is None:
            payment.delete()
            update_order_charge_data(order)
            return OrderCheckPrepayment(order=SyncWebhookControlContext(order))

        reconciled = get_reconciled_amount(response)
        if reconciled > 0:
            payment.captured_amount = reconciled
            payment.total = reconciled
            payment.charge_status = ChargeStatus.FULLY_CHARGED
        else:
            payment.captured_amount = Decimal(0)
            payment.total = Decimal(0)
            payment.charge_status = ChargeStatus.NOT_CHARGED
        payment.save(
            update_fields=[
                "captured_amount",
                "total",
                "charge_status",
                "modified_at",
            ]
        )

        update_order_charge_data(order)

        return OrderCheckPrepayment(order=SyncWebhookControlContext(order))
