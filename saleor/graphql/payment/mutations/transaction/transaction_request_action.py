from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional, cast

import graphene
from django.core.exceptions import ValidationError

from .....app.models import App
from .....core.prices import quantize_price
from .....giftcard.const import GIFT_CARD_PAYMENT_GATEWAY_ID
from .....giftcard.gateway import (
    cancel_gift_card_transaction,
    refund_gift_card_transaction,
)
from .....order.models import Order
from .....page.models import Page
from .....payment import PaymentError, TransactionAction
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
from ....core.validators import validate_one_of_args_is_in_mutation
from ....plugins.dataloaders import get_plugin_manager_promise
from ....site.dataloaders import get_site_promise
from ...enums import TransactionActionEnum
from ...types import TransactionItem
from ...utils import validate_and_resolve_refund_reason_context
from .utils import create_transaction_event_requested, get_transaction_item

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
        refund_reason = graphene.String(
            description="Reason of the refund" + ADDED_IN_322,
            required=False,
        )
        refund_reason_reference = graphene.ID(
            description="ID of a `Page` (Model) to reference in reason." + ADDED_IN_322,
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
        transaction = action_kwargs["transaction"]
        app_identifier = (
            GIFT_CARD_PAYMENT_GATEWAY_ID
            if transaction.app_identifier == GIFT_CARD_PAYMENT_GATEWAY_ID
            else None
        )

        if action == TransactionAction.CANCEL:
            action_value = action_value or transaction.authorized_value
            action_value = min(action_value, transaction.authorized_value)
            request_event = cls.create_transaction_event_requested(
                transaction,
                action_value,
                action,
                user=user,
                app=app,
                app_identifier=app_identifier,
            )
            if transaction.app_identifier == GIFT_CARD_PAYMENT_GATEWAY_ID:
                cancel_gift_card_transaction(transaction, request_event)
            else:
                request_cancelation_action(
                    **action_kwargs,
                    cancel_value=action_value,
                    request_event=request_event,
                    action=action,
                )
        elif action == TransactionAction.CHARGE:
            action_value = action_value or transaction.authorized_value
            action_value = min(action_value, transaction.authorized_value)
            request_event = cls.create_transaction_event_requested(
                transaction, action_value, TransactionAction.CHARGE, user=user, app=app
            )
            request_charge_action(
                **action_kwargs, charge_value=action_value, request_event=request_event
            )
        elif action == TransactionAction.REFUND:
            action_value = action_value or transaction.charged_value
            action_value = min(action_value, transaction.charged_value)
            request_event = cls.create_transaction_event_requested(
                transaction,
                action_value,
                action,
                user=user,
                app=app,
                app_identifier=app_identifier,
                reason=reason,
                reason_reference=reason_reference,
            )
            if transaction.app_identifier == GIFT_CARD_PAYMENT_GATEWAY_ID:
                refund_gift_card_transaction(transaction, request_event)
            else:
                request_refund_action(
                    **action_kwargs,
                    refund_value=action_value,
                    request_event=request_event,
                )

    @classmethod
    def create_transaction_event_requested(
        cls,
        transaction,
        action_value,
        action,
        user=None,
        app=None,
        app_identifier=None,
        reason=None,
        reason_reference: Page | None = None,
    ):
        return create_transaction_event_requested(
            transaction,
            action_value,
            action,
            user=user,
            app=app,
            app_identifier=app_identifier,
            reason=reason,
            reason_reference=reason_reference,
        )

    @classmethod
    def _validate_reason_and_event(cls, input: dict[str, Any]):
        action_type = input["action_type"]
        reason = input.get("refund_reason")
        reason_reference_id = input.get("refund_reason_reference")

        reason_exists = reason or reason_reference_id

        if reason_exists and action_type != TransactionAction.REFUND:
            errors = {}

            if reason:
                errors["refund_reason"] = ValidationError(
                    f"Reason can be set only for {TransactionActionEnum.REFUND.name} action.",
                    code=TransactionRequestActionErrorCode.INVALID.value,
                )

            if reason_reference_id:
                errors["refund_reason_reference"] = ValidationError(
                    f"Reason reference can be set only for {TransactionActionEnum.REFUND.name} action.",
                    code=TransactionRequestActionErrorCode.INVALID.value,
                )

            raise ValidationError(errors)

    @classmethod
    def _prepare_refund_reason(cls, info: ResolveInfo, /, **data):
        reason_reference_id = data.get("refund_reason_reference")

        requestor_is_app = info.context.app is not None
        requestor_is_user = info.context.user is not None and not requestor_is_app

        site = get_site_promise(info.context).get()

        refund_reason_context = validate_and_resolve_refund_reason_context(
            reason_reference_id=reason_reference_id,
            requestor_is_user=bool(requestor_is_user),
            refund_reference_field_name="refund_reason_reference",
            error_code_enum=TransactionRequestActionErrorCode,
            site_settings=site.settings,
        )

        refund_reason_reference_type = refund_reason_context[
            "refund_reason_reference_type"
        ]

        reason_reference_instance: Page | None = None

        if refund_reason_context["should_apply"]:
            try:
                reason_reference_pk = cls.get_global_id_or_error(
                    str(reason_reference_id), only_type="Page", field="reason_reference"
                )

                reason_reference_instance = Page.objects.get(
                    pk=reason_reference_pk, page_type=refund_reason_reference_type.pk
                )

            except (Page.DoesNotExist, ValueError):
                raise ValidationError(
                    {
                        "refund_reason_reference": ValidationError(
                            "Invalid reason reference.",
                            code=TransactionRequestActionErrorCode.INVALID.value,
                        )
                    }
                ) from None

        return reason_reference_instance

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        id = data.get("id")
        token = data.get("token")
        action_type = data["action_type"]
        action_value = data.get("amount")
        reason = data.get("refund_reason")

        cls._validate_reason_and_event(data)

        reason_reference_instance = (
            cls._prepare_refund_reason(info, **data)
            if action_type == TransactionAction.REFUND
            else None
        )

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
