from decimal import Decimal

import graphene
from django.core.exceptions import ValidationError

from ....order.error_codes import OrderErrorCode
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
from ..types import Fulfillment, Order


class OrderAddPrepayment(BaseMutation):
    order = graphene.Field(Order, description="Order the prepayment was added to.")

    class Arguments:
        order_id = graphene.ID(required=True, description="ID of the order.")
        fulfillment_id = graphene.ID(
            required=False,
            description=(
                "ID of the fulfillment this prepayment is for. "
                "If omitted, the prepayment is treated as a deposit payment."
            ),
        )
        psp_reference = graphene.String(
            required=True,
            description="Xero bank transaction ID for this prepayment.",
        )

    class Meta:
        description = (
            "Add a Xero prepayment to an order. If fulfillment_id is provided, "
            "the prepayment is a proforma payment for that fulfillment. Otherwise "
            "it is a deposit payment. Deposit prepayments cannot be added after "
            "any fulfillment prepayment exists on the order."
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
        fulfillment_id=None,
    ):
        order = cls.get_node_or_error(info, order_id, only_type=Order)
        cls.check_channel_permissions(info, [order.channel_id])

        has_fulfillments = order.fulfillments.exists()

        fulfillment = None
        if has_fulfillments:
            if not fulfillment_id:
                raise ValidationError(
                    "This order has fulfillments. You must specify a fulfillment_id "
                    "for the prepayment.",
                    code=OrderErrorCode.INVALID.value,
                )
            fulfillment = cls.get_node_or_error(
                info, fulfillment_id, only_type=Fulfillment
            )
            if fulfillment.order_id != order.pk:
                raise ValidationError(
                    "Fulfillment does not belong to this order.",
                    code=OrderErrorCode.INVALID.value,
                )
        elif fulfillment_id:
            raise ValidationError(
                "Cannot add a fulfillment prepayment: this order has no fulfillments. "
                "Prepayments without a fulfillment are deposit payments.",
                code=OrderErrorCode.INVALID.value,
            )

        already_exists = Payment.objects.filter(
            psp_reference=psp_reference,
            gateway=CustomPaymentChoices.XERO,
        ).exists()
        if already_exists:
            raise ValidationError(
                "A prepayment with this psp_reference already exists.",
                code=OrderErrorCode.INVALID.value,
            )

        manager = get_plugin_manager_promise(info.context).get()
        response = manager.xero_check_prepayment_status(psp_reference)
        if response is None:
            raise ValidationError(
                "Prepayment not found in Xero. Check the bank transaction ID.",
                code=OrderErrorCode.INVALID.value,
            )

        reconciled = get_reconciled_amount(response)
        Payment.objects.create(
            order=order,
            fulfillment=fulfillment,
            gateway=CustomPaymentChoices.XERO,
            psp_reference=psp_reference,
            captured_amount=reconciled if reconciled > 0 else Decimal(0),
            total=reconciled if reconciled > 0 else Decimal(0),
            charge_status=(
                ChargeStatus.FULLY_CHARGED
                if reconciled > 0
                else ChargeStatus.NOT_CHARGED
            ),
            currency=order.currency,
        )

        return OrderAddPrepayment(order=SyncWebhookControlContext(order))
