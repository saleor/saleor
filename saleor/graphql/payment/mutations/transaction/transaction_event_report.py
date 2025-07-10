from typing import TYPE_CHECKING, cast

import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from .....app.models import App
from .....core.exceptions import PermissionDenied
from .....core.prices import quantize_price
from .....core.tracing import traced_atomic_transaction
from .....core.utils.events import call_event
from .....order import models as order_models
from .....order.utils import (
    calculate_order_granted_refund_status,
)
from .....payment import OPTIONAL_AMOUNT_EVENTS, TransactionEventType
from .....payment import models as payment_models
from .....payment.interface import PaymentMethodDetails
from .....payment.lock_objects import (
    transaction_item_qs_select_for_update,
)
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from .....payment.utils import (
    authorization_success_already_exists,
    create_failed_transaction_event,
    get_already_existing_event,
    get_transaction_event_amount,
    process_order_or_checkout_with_transaction,
    truncate_transaction_event_message,
    update_transaction_item_with_payment_method_details,
)
from .....permission.auth_filters import AuthorizationFilters
from .....permission.enums import PaymentPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_322
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import TransactionEventReportErrorCode
from ....core.mutations import DeprecatedModelMutation
from ....core.scalars import UUID, DateTime, PositiveDecimal
from ....core.types import NonNullList
from ....core.types import common as common_types
from ....core.utils import WebhookEventInfo
from ....core.validators import validate_one_of_args_is_in_mutation
from ....meta.inputs import MetadataInput, MetadataInputDescription
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import TransactionActionEnum, TransactionEventTypeEnum
from ...types import TransactionEvent, TransactionItem
from ...utils import check_if_requestor_has_access
from .shared import (
    PaymentMethodDetailsInput,
    get_payment_method_details,
    validate_payment_method_details_input,
)
from .utils import get_transaction_item

if TYPE_CHECKING:
    from .....plugins.manager import PluginsManager


class TransactionEventReport(DeprecatedModelMutation):
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
        psp_reference = graphene.String(
            description="PSP Reference of the event to report.", required=True
        )
        type = graphene.Argument(
            TransactionEventTypeEnum,
            required=True,
            description="Current status of the event to report.",
        )
        amount = PositiveDecimal(
            description=(
                "The amount of the event to report. \n\nRequired for all `REQUEST`, "
                "`SUCCESS`, `ACTION_REQUIRED`, and `ADJUSTMENT` events. For other events, "
                "the amount will be calculated based on the previous events with "
                "the same pspReference. "
                "If not possible to calculate, the mutation will return an error."
            ),
            required=False,
        )
        time = DateTime(
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
        message = graphene.String(
            description=(
                "The message related to the event. The maximum length is 512 "
                "characters; any text exceeding this limit will be truncated."
            )
        )
        available_actions = graphene.List(
            graphene.NonNull(TransactionActionEnum),
            description="List of all possible actions for the transaction",
        )
        transaction_metadata = NonNullList(
            MetadataInput,
            description="Fields required to update the transaction metadata. "
            f"{MetadataInputDescription.PUBLIC_METADATA_INPUT}",
            required=False,
        )
        transaction_private_metadata = NonNullList(
            MetadataInput,
            description="Fields required to update the transaction private metadata."
            f"\n\n{MetadataInputDescription.PRIVATE_METADATA_INPUT}",
            required=False,
        )
        payment_method_details = PaymentMethodDetailsInput(
            description="Details of the payment method used for the transaction."
            + ADDED_IN_322,
            required=False,
        )

    class Meta:
        description = (
            "Report the event for the transaction."
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
        support_meta_field = True
        support_private_meta_field = True
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.TRANSACTION_ITEM_METADATA_UPDATED,
                description=(
                    "Optionally called when transaction's metadata was updated."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_FULLY_PAID,
                description=(
                    "Optionally called when the checkout charge status "
                    "changed to `FULL` or `OVERCHARGED`."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ORDER_UPDATED,
                description=(
                    "Optionally called when the transaction is related to the order "
                    "and the order was updated."
                ),
            ),
        ]

    @classmethod
    def _update_mutation_arguments_and_fields(cls, arguments, fields):
        cls._meta.arguments.update(arguments)

    @classmethod
    def update_transaction(
        cls,
        manager: "PluginsManager",
        transaction: payment_models.TransactionItem,
        transaction_event: payment_models.TransactionEvent,
        available_actions: list[str] | None = None,
        app: App | None = None,
        metadata: list[MetadataInput] | None = None,
        private_metadata: list[MetadataInput] | None = None,
        payment_details_data: PaymentMethodDetails | None = None,
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
            "modified_at",
            "metadata",
            "private_metadata",
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

        if payment_details_data:
            fields_to_update.extend(
                update_transaction_item_with_payment_method_details(
                    transaction, payment_details_data
                )
            )

        recalculate_transaction_amounts(transaction, save=False)
        transaction_has_assigned_app = transaction.app_id or transaction.app_identifier
        if app and not transaction.user_id and not transaction_has_assigned_app:
            transaction.app_id = app.pk
            transaction.app_identifier = app.identifier
            fields_to_update.append("app")
            fields_to_update.append("app_identifier")
        transaction.save(update_fields=fields_to_update)
        if metadata:
            call_event(manager.transaction_item_metadata_updated, transaction)

    @classmethod
    def get_related_granted_refund(
        cls, event_psp_reference: str, transaction: payment_models.TransactionItem
    ) -> order_models.OrderGrantedRefund | None:
        request_refund = (
            payment_models.TransactionEvent.objects.filter(
                psp_reference=event_psp_reference,
                transaction_id=transaction.pk,
                type=TransactionEventType.REFUND_REQUEST,
            )
            .select_related("related_granted_refund")
            .last()
        )
        return request_refund.related_granted_refund if request_refund else None

    @classmethod
    def clean_amount_value(
        cls, amount: float | None, event_type: str, psp_reference: str, currency: str
    ):
        if amount is None:
            if event_type not in OPTIONAL_AMOUNT_EVENTS:
                raise ValidationError(
                    {
                        "amount": ValidationError(
                            f"The `amount` field is required for {event_type} event.",
                            code=TransactionEventReportErrorCode.REQUIRED.value,
                        )
                    }
                )
            try:
                amount = get_transaction_event_amount(event_type, psp_reference)
            except ValueError as e:
                raise ValidationError(
                    {
                        "amount": ValidationError(
                            str(e),
                            code=TransactionEventReportErrorCode.REQUIRED.value,
                        )
                    },
                ) from e
        return quantize_price(amount, currency)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        root,
        info: ResolveInfo,
        /,
        *,
        psp_reference,
        type,
        amount=None,
        token=None,
        id=None,
        time=None,
        external_url=None,
        message=None,
        available_actions=None,
        transaction_metadata: list[MetadataInput] | None = None,
        transaction_private_metadata: list[MetadataInput] | None = None,
        payment_method_details: PaymentMethodDetailsInput | None = None,
    ):
        validate_one_of_args_is_in_mutation("id", id, "token", token)
        transaction = get_transaction_item(id, token)
        user = info.context.user
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()

        if not check_if_requestor_has_access(
            transaction=transaction, user=user, app=app
        ):
            raise PermissionDenied(
                permissions=[
                    AuthorizationFilters.OWNER,
                    PaymentPermissions.HANDLE_PAYMENTS,
                ]
            )

        amount = cls.clean_amount_value(
            amount, type, psp_reference, transaction.currency
        )
        app_identifier = None
        if app and app.identifier:
            app_identifier = app.identifier

        related_granted_refund = None
        if type in TransactionEventType.REFUND_RELATED_EVENT_TYPES:
            related_granted_refund = cls.get_related_granted_refund(
                psp_reference, transaction
            )

        payment_details_data: PaymentMethodDetails | None = None
        if payment_method_details:
            validate_payment_method_details_input(
                payment_method_details, TransactionEventReportErrorCode
            )
            payment_details_data = get_payment_method_details(payment_method_details)

        message = (
            truncate_transaction_event_message(message) if message is not None else ""
        )
        transaction_event_data = {
            "psp_reference": psp_reference,
            "type": type,
            "amount_value": amount,
            "currency": transaction.currency,
            "created_at": time or timezone.now(),
            "external_url": external_url or "",
            "message": message,
            "transaction": transaction,
            "app_identifier": app_identifier,
            "app": app,
            "user": user,
            "include_in_calculations": True,
            "related_granted_refund": related_granted_refund,
        }
        transaction_event = cls.get_instance(info, **transaction_event_data)
        transaction_event = cast(payment_models.TransactionEvent, transaction_event)
        transaction_event = cls.construct_instance(
            transaction_event, transaction_event_data
        )

        metadata_collection = cls.create_metadata_from_graphql_input(
            transaction_metadata, error_field_name="metadata"
        )
        private_metadata_collection = cls.create_metadata_from_graphql_input(
            transaction_private_metadata,
            error_field_name="private_metadata",
        )

        cls.validate_and_update_metadata(
            transaction, metadata_collection, private_metadata_collection
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
            _transaction = (
                transaction_item_qs_select_for_update()
                .filter(pk=transaction.pk)
                .first()
            )

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
            if related_granted_refund:
                calculate_order_granted_refund_status(related_granted_refund)
            raise ValidationError({error_field: ValidationError(error_msg, error_code)})
        if not already_processed:
            previous_authorized_value = transaction.authorized_value
            previous_charged_value = transaction.charged_value
            previous_refunded_value = transaction.refunded_value
            cls.update_transaction(
                manager,
                transaction,
                transaction_event,
                available_actions=available_actions,
                app=app,
                metadata=transaction_metadata,
                private_metadata=transaction_private_metadata,
                payment_details_data=payment_details_data,
            )
            process_order_or_checkout_with_transaction(
                transaction,
                manager,
                user,
                app,
                previous_authorized_value,
                previous_charged_value,
                previous_refunded_value,
                related_granted_refund=related_granted_refund,
            )
        else:
            updated_fields = []
            if available_actions is not None and set(
                transaction.available_actions
            ) != set(available_actions):
                transaction.available_actions = available_actions
                updated_fields.append("available_actions")

            if payment_details_data:
                updated_fields.extend(
                    update_transaction_item_with_payment_method_details(
                        transaction, payment_details_data
                    )
                )
            if updated_fields:
                transaction.save(update_fields=updated_fields)

        return cls(
            already_processed=already_processed,
            transaction=transaction,
            transaction_event=transaction_event,
            errors=[],
        )
