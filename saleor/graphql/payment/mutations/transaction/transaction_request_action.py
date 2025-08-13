import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, cast

import graphene
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError

from .....app.models import App
from .....core.prices import quantize_price
from .....order.models import Order
from .....page.models import Page
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
from ....core.descriptions import ADDED_IN_322
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.mutations import BaseMutation
from ....core.scalars import UUID, PositiveDecimal
from ....core.types import common as common_types
from ....core.utils import from_global_id_or_error
from ....core.validators import validate_one_of_args_is_in_mutation
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
            description=(
                "The ID of the transaction. One of field id or token is required."
            ),
            required=False,
        )
        token = UUID(
            description=(
                "The token of the transaction. One of field id or token is required."
            ),
            required=False,
        )
        action_type = graphene.Argument(
            TransactionActionEnum,
            required=True,
            description="Determines the action type.",
        )
        amount = PositiveDecimal(
            description=(
                "Transaction request amount. If empty, maximal possible "
                "amount will be used."
            ),
            required=False,
        )
        reason = graphene.String(
            description="Reason of the refund" + ADDED_IN_322,
            required=False,
        )
        reason_reference = graphene.ID(
            description="ID of Model to reference in reason." + ADDED_IN_322,
            required=False,
        )

    class Meta:
        description = "Request an action for payment transaction."
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.TransactionRequestActionError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)

    @classmethod
    def handle_transaction_action(
        cls,
        action,
        action_kwargs,
        action_value: Decimal | None,
        user: Optional["User"],
        app: App | None,
        reason: str | None = None,
        reason_reference: Page | None = None,
    ):
        if action == TransactionAction.CANCEL:
            transaction = action_kwargs["transaction"]
            action_value = action_value or transaction.authorized_value
            action_value = min(action_value, transaction.authorized_value)
            request_event = cls.create_transaction_event_requested(
                transaction, action_value, action, user=user, app=app
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
                transaction,
                action_value,
                TransactionAction.REFUND,
                user=user,
                app=app,
                reason=reason,
                reason_reference=reason_reference,
            )
            request_refund_action(
                **action_kwargs, refund_value=action_value, request_event=request_event
            )

    @classmethod
    def create_transaction_event_requested(
        cls,
        transaction,
        action_value,
        action,
        user=None,
        app=None,
        reason=None,
        reason_reference: Page | None = None,
    ):
        message: str | None = None
        reason_reference_to_set = None

        if action == TransactionAction.CANCEL:
            type = TransactionEventType.CANCEL_REQUEST
        elif action == TransactionAction.CHARGE:
            type = TransactionEventType.CHARGE_REQUEST
        elif action == TransactionAction.REFUND:
            type = TransactionEventType.REFUND_REQUEST
            message = reason or None
            reason_reference_to_set = reason_reference or None
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
            idempotency_key=str(uuid.uuid4()),
            message=message,
            reason_reference=reason_reference_to_set,
        )

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        id = data.get("id")
        token = data.get("token")
        action_type = data["action_type"]
        action_value = data.get("amount")
        reason = data.get("reason")
        reason_reference_id = data.get("reason_reference")
        if len(reason_reference_id) == 0:
            reason_reference_id = None

        requestor_is_app = info.context.app is not None
        requestor_is_user = info.context.user is not None and not requestor_is_app

        settings = Site.objects.get_current().settings
        refund_reason_reference_type = settings.refund_reason_reference_type

        # It works as following:
        # If it's not configured, it's optional
        # If it's configured, it's required for staff user
        # It's never required for the app
        is_passing_reason_reference_required = refund_reason_reference_type is not None

        if (
            is_passing_reason_reference_required
            and reason_reference_id is None
            and requestor_is_user
        ):
            raise ValidationError(
                {
                    "reason_reference": ValidationError(
                        "Reason reference is required when refund reason reference type is configured.",
                        code=TransactionRequestActionErrorCode.REQUIRED.value,
                    )
                }
            ) from None

        # If feature is not enabled, ignore it from the input
        if not is_passing_reason_reference_required:
            reason_reference_id = None

        reason_reference_instance = None

        if reason_reference_id:
            try:
                type_, reason_reference_pk = from_global_id_or_error(
                    reason_reference_id, only_type="Page"
                )
                if reason_reference_pk:
                    reason_reference_instance = Page.objects.get(pk=reason_reference_pk)
            except (Page.DoesNotExist, ValueError):
                raise ValidationError(
                    {
                        "reason_reference": ValidationError(
                            "Invalid reason reference.",
                            code=TransactionRequestActionErrorCode.INVALID.value,
                        )
                    }
                ) from None

        validate_one_of_args_is_in_mutation("id", id, "token", token)
        transaction = get_transaction_item(id, token)
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

        if action_value is not None:
            action_value = quantize_price(action_value, transaction.currency)

        action_kwargs = {
            "channel_slug": channel_slug,
            "user": user,
            "app": app,
            "transaction": transaction,
            "manager": manager,
        }

        try:
            cls.handle_transaction_action(
                action_type,
                action_kwargs,
                action_value,
                user,
                app,
                reason,
                reason_reference_instance,
            )
        except PaymentError as e:
            error_enum = TransactionRequestActionErrorCode
            code = error_enum.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.value
            raise ValidationError(str(e), code=code) from e
        return TransactionRequestAction(transaction=transaction)
