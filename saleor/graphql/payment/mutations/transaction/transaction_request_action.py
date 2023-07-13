from decimal import Decimal
from typing import TYPE_CHECKING, Optional, cast

import graphene
from django.core.exceptions import ValidationError

from .....app.models import App
from .....order.models import Order
from .....payment import PaymentError, TransactionAction, TransactionEventType
from .....payment.error_codes import TransactionRequestActionErrorCode
from .....payment.gateway import (
    request_cancelation_action,
    request_charge_action,
    request_refund_action,
)
from .....permission.enums import PaymentPermissions
from ....app.dataloaders import get_app_promise
from ....checkout.types import Checkout
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_34, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.mutations import BaseMutation
from ....core.scalars import PositiveDecimal
from ....core.types import common as common_types
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import TransactionActionEnum
from ...types import TransactionItem
from .utils import get_transaction_item

if TYPE_CHECKING:
    from .....account.models import User


class TransactionRequestAction(BaseMutation):
    transaction = graphene.Field(TransactionItem)

    class Arguments:
        id = graphene.ID(
            description="The ID of the transaction.",
            required=True,
        )
        action_type = graphene.Argument(
            TransactionActionEnum,
            required=True,
            description="Determines the action type.",
        )
        amount = PositiveDecimal(
            description=(
                "Transaction request amount. If empty for refund or capture, maximal "
                "possible amount will be used."
            )
        )

    class Meta:
        description = (
            "Request an action for payment transaction." + ADDED_IN_34 + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.TransactionRequestActionError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)

    @classmethod
    def handle_transaction_action(
        cls,
        action,
        action_kwargs,
        action_value: Optional[Decimal],
        user: Optional["User"],
        app: Optional[App],
    ):
        if action == TransactionAction.CANCEL:
            transaction = action_kwargs["transaction"]
            request_event = cls.create_transaction_event_requested(
                transaction, 0, action, user=user, app=app
            )
            request_cancelation_action(
                **action_kwargs,
                cancel_value=action_value,
                request_event=request_event,
                action=action,
            )
        elif action == TransactionAction.CHARGE:
            transaction = action_kwargs["transaction"]
            action_value = action_value or transaction.authorized_value
            action_value = min(action_value, transaction.authorized_value)
            request_event = cls.create_transaction_event_requested(
                transaction, action_value, TransactionAction.CHARGE, user=user, app=app
            )
            request_charge_action(
                **action_kwargs, charge_value=action_value, request_event=request_event
            )
        elif action == TransactionAction.REFUND:
            transaction = action_kwargs["transaction"]
            action_value = action_value or transaction.charged_value
            action_value = min(action_value, transaction.charged_value)
            request_event = cls.create_transaction_event_requested(
                transaction, action_value, TransactionAction.REFUND, user=user, app=app
            )
            request_refund_action(
                **action_kwargs, refund_value=action_value, request_event=request_event
            )

    @classmethod
    def create_transaction_event_requested(
        cls, transaction, action_value, action, user=None, app=None
    ):
        if action == TransactionAction.CANCEL:
            type = TransactionEventType.CANCEL_REQUEST
        elif action == TransactionAction.CHARGE:
            type = TransactionEventType.CHARGE_REQUEST
        elif action == TransactionAction.REFUND:
            type = TransactionEventType.REFUND_REQUEST
        else:
            raise ValidationError(
                {
                    "actionType": ValidationError(
                        "Incorrect action.",
                        code=TransactionRequestActionErrorCode.INVALID.value,
                    )
                }
            )
        return transaction.events.create(
            amount_value=action_value,
            currency=transaction.currency,
            type=type,
            user=user,
            app=app,
            app_identifier=app.identifier if app else None,
        )

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        id = data["id"]
        action_type = data["action_type"]
        action_value = data.get("amount")
        transaction = get_transaction_item(id)
        if transaction.order_id:
            order = cast(Order, transaction.order)
            channel = order.channel
        else:
            checkout = cast(Checkout, transaction.checkout)
            channel = checkout.channel
        cls.check_channel_permissions(info, [channel.id])
        channel_slug = channel.slug
        user = info.context.user
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        action_kwargs = {
            "channel_slug": channel_slug,
            "user": user,
            "app": app,
            "transaction": transaction,
            "manager": manager,
        }

        try:
            cls.handle_transaction_action(
                action_type, action_kwargs, action_value, user, app
            )
        except PaymentError as e:
            error_enum = TransactionRequestActionErrorCode
            code = error_enum.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.value
            raise ValidationError(str(e), code=code)
        return TransactionRequestAction(transaction=transaction)
