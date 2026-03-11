import graphene
from django.core.exceptions import ValidationError

from ....order.error_codes import OrderErrorCode
from ....order.utils import update_order_charge_data
from ....payment import ChargeStatus, CustomPaymentChoices
from ....payment.models import Payment
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order


class OrderDeletePrepayment(BaseMutation):
    order = graphene.Field(Order, description="Order the prepayment was deleted from.")

    class Arguments:
        order_id = graphene.ID(required=True, description="ID of the order.")
        psp_reference = graphene.String(
            required=True,
            description="Xero bank transaction ID of the prepayment to delete.",
        )

    class Meta:
        description = (
            "Delete an unpaid Xero prepayment from an order. "
            "The prepayment must have been voided in Xero first — "
            "this is verified by checking the prepayment status live."
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

        if payment.charge_status != ChargeStatus.NOT_CHARGED:
            raise ValidationError(
                "Cannot delete a prepayment that has already been paid.",
                code=OrderErrorCode.INVALID.value,
            )

        manager = get_plugin_manager_promise(info.context).get()
        response = manager.xero_check_prepayment_status(psp_reference)
        if response is not None:
            raise ValidationError(
                "Cannot delete: the prepayment still exists in Xero. "
                "Void the prepayment in Xero before deleting it here.",
                code=OrderErrorCode.INVALID.value,
            )

        payment.delete()

        update_order_charge_data(order)

        return OrderDeletePrepayment(order=SyncWebhookControlContext(order))
