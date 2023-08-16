from typing import Optional, cast

import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from .....app.models import App
from .....checkout.actions import transaction_amounts_for_checkout_updated
from .....core.exceptions import PermissionDenied
from .....core.tracing import traced_atomic_transaction
from .....order import models as order_models
from .....order.actions import order_transaction_updated
from .....order.fetch import fetch_order_info
from .....order.search import update_order_search_vector
from .....order.utils import updates_amounts_for_order
from .....payment import TransactionEventType
from .....payment import models as payment_models
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from .....payment.utils import (
    authorization_success_already_exists,
    create_failed_transaction_event,
    get_already_existing_event,
)
from .....permission.auth_filters import AuthorizationFilters
from .....permission.enums import PaymentPermissions
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_313, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import TransactionEventReportErrorCode
from ....core.mutations import ModelMutation
from ....core.scalars import PositiveDecimal
from ....core.types import common as common_types
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import TransactionActionEnum, TransactionEventTypeEnum
from ...types import TransactionEvent, TransactionItem
from ...utils import check_if_requestor_has_access
from .utils import get_transaction_item


class TransactionEventReport(ModelMutation):
    already_processed = graphene.Boolean(
        description="Defines if the reported event hasn't been processed earlier."
    )
    transaction = graphene.Field(
        TransactionItem, description="The transaction related to the reported event."
    )
    transaction_event = graphene.Field(
        TransactionEvent,
        description=(
            "The event assigned to this report. if `alreadyProcessed` is set to `true`,"
            " the previously processed event will be returned."
        ),
    )

    class Arguments:
        id = graphene.ID(
            description="The ID of the transaction.",
            required=True,
        )
        psp_reference = graphene.String(
            description="PSP Reference of the event to report.", required=True
        )
        type = graphene.Argument(
            TransactionEventTypeEnum,
            required=True,
            description="Current status of the event to report.",
        )
        amount = PositiveDecimal(
            description="The amount of the event to report.", required=True
        )
        time = graphene.DateTime(
            description=(
                "The time of the event to report. If not provide, "
                "the current time will be used."
            )
        )
        external_url = graphene.String(
            description=(
                "The url that will allow to redirect user to "
                "payment provider page with event details."
            )
        )
        message = graphene.String(description="The message related to the event.")
        available_actions = graphene.List(
            graphene.NonNull(TransactionActionEnum),
            description="List of all possible actions for the transaction",
        )

    class Meta:
        description = (
            "Report the event for the transaction."
            + ADDED_IN_313
            + PREVIEW_FEATURE
            + "\n\nRequires the following permissions: "
            + f"{AuthorizationFilters.OWNER.name} "
            + f"and {PaymentPermissions.HANDLE_PAYMENTS.name} for apps, "
            f"{PaymentPermissions.HANDLE_PAYMENTS.name} for staff users. "
            f"Staff user cannot update a transaction that is owned by the app."
        )
        error_type_class = common_types.TransactionEventReportError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)
        doc_category = DOC_CATEGORY_PAYMENTS
        model = payment_models.TransactionEvent
        object_type = TransactionEvent
        auto_permission_message = False

    @classmethod
    def _update_mutation_arguments_and_fields(cls, arguments, fields):
        cls._meta.arguments.update(arguments)

    @classmethod
    def update_transaction(
        cls,
        transaction: payment_models.TransactionItem,
        transaction_event: payment_models.TransactionEvent,
        available_actions: Optional[list[str]] = None,
        app: Optional["App"] = None,
    ):
        fields_to_update = [
            "authorized_value",
            "charged_value",
            "refunded_value",
            "canceled_value",
            "authorize_pending_value",
            "charge_pending_value",
            "refund_pending_value",
            "cancel_pending_value",
        ]

        if (
            transaction_event.type
            in [
                TransactionEventType.AUTHORIZATION_REQUEST,
                TransactionEventType.AUTHORIZATION_SUCCESS,
                TransactionEventType.CHARGE_REQUEST,
                TransactionEventType.CHARGE_SUCCESS,
            ]
            and not transaction.psp_reference
        ):
            transaction.psp_reference = transaction_event.psp_reference
            fields_to_update.append("psp_reference")

        if available_actions is not None:
            transaction.available_actions = available_actions
            fields_to_update.append("available_actions")

        recalculate_transaction_amounts(transaction, save=False)
        transaction_has_assigned_app = transaction.app_id or transaction.app_identifier
        if app and not transaction.user_id and not transaction_has_assigned_app:
            transaction.app_id = app.pk
            transaction.app_identifier = app.identifier
            fields_to_update.append("app")
            fields_to_update.append("app_identifier")
        transaction.save(update_fields=fields_to_update)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        root,
        info: ResolveInfo,
        /,
        *,
        id,
        psp_reference,
        type,
        amount,
        time=None,
        external_url=None,
        message=None,
        available_actions=None,
    ):
        user = info.context.user
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()

        transaction = get_transaction_item(id)

        if not check_if_requestor_has_access(
            transaction=transaction, user=user, app=app
        ):
            raise PermissionDenied(
                permissions=[
                    AuthorizationFilters.OWNER,
                    PaymentPermissions.HANDLE_PAYMENTS,
                ]
            )

        app_identifier = None
        if app and app.identifier:
            app_identifier = app.identifier

        transaction_event_data = {
            "psp_reference": psp_reference,
            "type": type,
            "amount_value": amount,
            "currency": transaction.currency,
            "created_at": time or timezone.now(),
            "external_url": external_url or "",
            "message": message or "",
            "transaction": transaction,
            "app_identifier": app_identifier,
            "app": app,
            "user": user,
            "include_in_calculations": True,
        }
        transaction_event = cls.get_instance(info, **transaction_event_data)
        transaction_event = cast(payment_models.TransactionEvent, transaction_event)
        transaction_event = cls.construct_instance(
            transaction_event, transaction_event_data
        )

        cls.clean_instance(info, transaction_event)

        if available_actions is not None:
            available_actions = list(set(available_actions))

        already_processed = False
        error_code = None
        error_msg = None
        error_field = None
        with traced_atomic_transaction():
            # The mutation can be called multiple times by the app. That can cause a
            # thread race. We need to be sure, that we will always create a single event
            # on our side for specific action.
            existing_event = get_already_existing_event(transaction_event)
            if existing_event and existing_event.amount != transaction_event.amount:
                error_code = TransactionEventReportErrorCode.INCORRECT_DETAILS.value
                error_msg = (
                    "The transaction with provided `pspReference` and "
                    "`type` already exists with different amount."
                )
                error_field = "pspReference"
            elif existing_event:
                already_processed = True
                transaction_event = existing_event
            elif (
                transaction_event.type == TransactionEventType.AUTHORIZATION_SUCCESS
                and authorization_success_already_exists(transaction.pk)
            ):
                error_code = TransactionEventReportErrorCode.ALREADY_EXISTS.value
                error_msg = (
                    "Event with `AUTHORIZATION_SUCCESS` already "
                    "reported for the transaction. Use "
                    "`AUTHORIZATION_ADJUSTMENT` to change the "
                    "authorization amount."
                )
                error_field = "type"
            else:
                transaction_event.save()

        if error_msg and error_code and error_field:
            create_failed_transaction_event(transaction_event, cause=error_msg)
            raise ValidationError({error_field: ValidationError(error_msg, error_code)})
        if not already_processed:
            previous_authorized_value = transaction.authorized_value
            previous_charged_value = transaction.charged_value
            previous_refunded_value = transaction.refunded_value
            cls.update_transaction(
                transaction,
                transaction_event,
                available_actions=available_actions,
                app=app,
            )
            if transaction.order_id:
                order = cast(order_models.Order, transaction.order)
                update_order_search_vector(order, save=False)
                updates_amounts_for_order(order, save=False)
                order.save(
                    update_fields=[
                        "total_charged_amount",
                        "charge_status",
                        "updated_at",
                        "total_authorized_amount",
                        "authorize_status",
                        "search_vector",
                    ]
                )
                order_info = fetch_order_info(order)
                order_transaction_updated(
                    order_info=order_info,
                    transaction_item=transaction,
                    manager=manager,
                    user=user,
                    app=app,
                    previous_authorized_value=previous_authorized_value,
                    previous_charged_value=previous_charged_value,
                    previous_refunded_value=previous_refunded_value,
                )
            if transaction.checkout_id:
                manager = get_plugin_manager_promise(info.context).get()
                transaction_amounts_for_checkout_updated(transaction, manager)
        elif available_actions is not None and set(
            transaction.available_actions
        ) != set(available_actions):
            transaction.available_actions = available_actions
            transaction.save(update_fields=["available_actions"])

        return cls(
            already_processed=already_processed,
            transaction=transaction,
            transaction_event=transaction_event,
            errors=[],
        )
