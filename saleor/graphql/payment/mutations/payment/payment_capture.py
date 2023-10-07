import graphene
from django.core.exceptions import ValidationError

from .....payment import PaymentError, gateway
from .....payment.error_codes import PaymentErrorCode
from .....permission.enums import OrderPermissions
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.mutations import BaseMutation
from ....core.scalars import PositiveDecimal
from ....core.types import common as common_types
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Payment


class PaymentCapture(BaseMutation):
    payment = graphene.Field(Payment, description="Updated payment.")

    class Arguments:
        payment_id = graphene.ID(required=True, description="Payment ID.")
        amount = PositiveDecimal(description="Transaction amount.")

    class Meta:
        description = "Captures the authorized payment amount."
        doc_category = DOC_CATEGORY_PAYMENTS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, amount=None, payment_id
    ):
        payment = cls.get_node_or_error(
            info, payment_id, field="payment_id", only_type=Payment
        )
        channel = payment.order.channel if payment.order else payment.checkout.channel
        cls.check_channel_permissions(info, [channel.id])
        channel_slug = channel.slug
        manager = get_plugin_manager_promise(info.context).get()
        try:
            gateway.capture(
                payment,
                manager,
                amount=amount,
                channel_slug=channel_slug,
            )
            payment.refresh_from_db()
        except PaymentError as e:
            raise ValidationError(str(e), code=PaymentErrorCode.PAYMENT_ERROR.value)
        return PaymentCapture(payment=payment)
