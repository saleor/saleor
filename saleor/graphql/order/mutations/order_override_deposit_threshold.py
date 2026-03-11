import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....order.error_codes import OrderErrorCode
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ..types import Order


class OrderOverrideDepositThreshold(BaseMutation):
    order = graphene.Field(Order, description="Order with updated deposit override.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order.")
        override = graphene.Boolean(
            required=True,
            description="Set to true to manually mark the deposit threshold as met.",
        )

    class Meta:
        description = "Manually override the deposit threshold check for an order."
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, id, override):  # type: ignore[override]
        order = cls.get_node_or_error(info, id, only_type=Order)
        cls.check_channel_permissions(info, [order.channel_id])

        if override and not order.deposit_required:
            raise ValidationError(
                "Cannot override deposit threshold: this order does not require a deposit.",
                code=OrderErrorCode.INVALID.value,
            )

        if override:
            if order.payments.xero_unpaid_deposits().exists():
                raise ValidationError(
                    "Cannot override deposit threshold while unpaid deposit "
                    "prepayments exist. Delete the unpaid prepayments first.",
                    code=OrderErrorCode.INVALID.value,
                )

        update_fields = ["deposit_threshold_met_override"]
        order.deposit_threshold_met_override = override
        if override and not order.deposit_paid_at:
            order.deposit_paid_at = timezone.now()
            update_fields.append("deposit_paid_at")
        order.save(update_fields=update_fields)

        return OrderOverrideDepositThreshold(order=SyncWebhookControlContext(order))
